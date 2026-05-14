"""main.py — FastAPI backend with session-based shared state.
All endpoints read/write the same session — no desync possible.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os, tempfile

from data import COURSES, MAJOR_REQUIREMENTS, MOCK_STUDENTS
from scheduler import SchedulingEngine
from tracker import RequirementTracker
from explainer import ExplanationModule
from chatbot import process_message
from session import get_or_create, StudentSession

app = FastAPI(title="Pathfinder API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── SCHEMAS ──────────────────────────────────────────
class StudentInput(BaseModel):
    student_name: str = "Student"
    major: str
    classification: str
    completed_courses: List[str] = []
    max_credits: int = 16
    prefers_morning: bool = False
    prefers_light_fridays: bool = False
    avoid_before: Optional[int] = None   # hard time constraint: no classes before N minutes
    avoid_after: Optional[int] = None    # hard time constraint: no classes ending after N minutes
    is_athlete: bool = False
    is_full_time: bool = True
    is_part_time: bool = False           # explicit opt-in; overrides full-time minimum
    session_id: Optional[str] = None

class ScheduleRequest(BaseModel):
    student: StudentInput
    return_alternatives: int = 3

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class RemoveCourseRequest(BaseModel):
    session_id: str
    course_code: str

class UpdateCompletedRequest(BaseModel):
    session_id: str
    completed_courses: List[str]


# ── HELPER ──────────────────────────────────────────
def _run_schedule(session: StudentSession):
    """Generate schedule and store in session. Single source of truth."""
    engine = SchedulingEngine(COURSES, MAJOR_REQUIREMENTS)
    tracker = RequirementTracker(COURSES, MAJOR_REQUIREMENTS)
    explainer = ExplanationModule(COURSES, MAJOR_REQUIREMENTS)
    prefs = session.known_preferences

    result = engine.generate(
        major=session.major,
        completed=session.completed_courses,
        classification=session.classification,
        max_credits=prefs.get("max_credits", 16),
        min_credits=session.min_credits(),
        prefers_morning=prefs.get("prefers_morning", False),
        prefers_light_fridays=prefs.get("prefers_light_fridays", False),
        avoid_before=prefs.get("avoid_before"),   # hard constraint (e.g. no 8am)
        avoid_after=prefs.get("avoid_after"),
    )
    for alt in result["alternatives"]:
        for sem in alt["semesters"]:
            for c in sem["courses"]:
                c["explanation"] = explainer.explain_course(
                    c["code"], session.major, session.completed_courses, prefs)

    progress = tracker.compute_progress(session.major, session.completed_courses)
    session.current_plan = result["best"]
    session.all_alternatives = result["alternatives"]
    session.active_alt_index = 0
    session.progress = progress
    return result, progress


# ── ROUTES ──────────────────────────────────────────
@app.get("/")
def root(): return {"message":"Pathfinder API v3.0 — Wittenberg University"}

@app.get("/api/majors")
def get_majors():
    return [{"id":k,"name":v["name"],"total_credits":v["total_credits"],
             "major_credits":v["major_credits"],"connections_credits":v["connections_credits"]}
            for k,v in MAJOR_REQUIREMENTS.items()]

@app.get("/api/courses")
def get_courses(): return COURSES

@app.get("/api/courses/{code}")
def get_course(code: str):
    c = code.upper()
    if c not in COURSES: raise HTTPException(404, f"Course {c} not found")
    return COURSES[c]

@app.get("/api/requirements/{major}")
def get_reqs(major: str):
    if major not in MAJOR_REQUIREMENTS: raise HTTPException(404)
    return MAJOR_REQUIREMENTS[major]

@app.get("/api/students")
def get_students(): return MOCK_STUDENTS


@app.post("/api/schedule/generate")
def generate(req: ScheduleRequest):
    if req.student.major not in MAJOR_REQUIREMENTS:
        raise HTTPException(400, f"Unsupported major: {req.student.major}")

    session = get_or_create(req.student.session_id)
    session.student_name = req.student.student_name
    session.major = req.student.major
    session.classification = req.student.classification
    session.completed_courses = list(req.student.completed_courses)
    session.is_athlete = req.student.is_athlete
    session.is_full_time = req.student.is_full_time
    session.is_part_time = req.student.is_part_time
    session.known_preferences["max_credits"] = req.student.max_credits
    session.known_preferences["prefers_morning"] = req.student.prefers_morning
    session.known_preferences["prefers_light_fridays"] = req.student.prefers_light_fridays
    # Preserve avoid_before/avoid_after only if explicitly provided
    if req.student.avoid_before is not None:
        session.known_preferences["avoid_before"] = req.student.avoid_before
    if req.student.avoid_after is not None:
        session.known_preferences["avoid_after"] = req.student.avoid_after

    result, progress = _run_schedule(session)

    return {
        "session_id": session.session_id,
        "student": req.student.model_dump(),
        "progress": progress,
        **result,
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Chat endpoint — reads and writes session state."""
    session = get_or_create(req.session_id)
    result = process_message(req.message, session, COURSES, MAJOR_REQUIREMENTS)

    response: Dict[str, Any] = {
        "session_id": session.session_id,
        "response_text": result["response_text"],
        "session_state": {
            "student_name": session.student_name,
            "major": session.major,
            "classification": session.classification,
            "completed_courses": session.completed_courses,
            "is_athlete": session.is_athlete,
        },
    }

    if result["should_regenerate"]:
        sched, progress = _run_schedule(session)
        response["schedule"] = sched
        response["progress"] = progress

    return response


@app.post("/api/courses/remove")
def remove_course(req: RemoveCourseRequest):
    """Remove a course from the active plan — with CORE protection."""
    session = get_or_create(req.session_id)
    code = req.course_code.upper()
    if COURSES.get(code, {}).get("core_protected", False):
        raise HTTPException(403, f"{code} is a mandatory requirement and cannot be removed.")
    if session.current_plan:
        for sem in session.current_plan.get("semesters", []):
            sem["courses"] = [c for c in sem["courses"] if c["code"] != code]
            sem["total_credits"] = sum(c["credits"] for c in sem["courses"])
    return {"message": f"Removed {code}", "session_id": session.session_id,
            "current_plan": session.current_plan}


@app.post("/api/completed/update")
def update_completed(req: UpdateCompletedRequest):
    """Update completed courses list and refresh progress."""
    session = get_or_create(req.session_id)
    session.completed_courses = list(req.completed_courses)
    if session.major:
        tracker = RequirementTracker(COURSES, MAJOR_REQUIREMENTS)
        session.progress = tracker.compute_progress(session.major, session.completed_courses)
    return {"session_id": session.session_id, "progress": session.progress}


class ToggleCompletedRequest(BaseModel):
    session_id: str
    course_code: str


@app.post("/api/completed/toggle")
def toggle_completed(req: ToggleCompletedRequest):
    """Toggle a course's completed status with prerequisite validation."""
    session = get_or_create(req.session_id)
    code = req.course_code.upper()
    if code not in COURSES:
        raise HTTPException(404, f"Course {code} not found in catalog")

    was_completed = code in session.completed_courses

    if was_completed:
        # Un-completing: check if any completed course depends on this one
        dependents = [
            c for c in session.completed_courses
            if code in COURSES.get(c, {}).get("prereqs", [])
        ]
        if dependents:
            dep_names = ", ".join(
                f"{d} ({COURSES[d]['name']})" for d in dependents
            )
            raise HTTPException(
                400,
                f"Cannot un-complete {code} — it is a prerequisite for "
                f"your completed course(s): {dep_names}. "
                f"Un-complete those first."
            )
        session.completed_courses = [c for c in session.completed_courses if c != code]
        action = "unmarked"
    else:
        # Completing: check all prereqs including OR-groups
        info = COURSES.get(code, {})
        prereqs = info.get("prereqs", [])
        any_list = info.get("prereqs_any", [])
        done_set = set(session.completed_courses)

        missing_all = [p for p in prereqs if p not in done_set]
        any_ok = not any_list or any(p in done_set for p in any_list)

        missing_msgs = []
        for p in missing_all:
            missing_msgs.append(f"{p} ({COURSES.get(p, {}).get('name', p)})")
        if not any_ok:
            missing_msgs.append(f"one of: {', '.join(any_list)}")

        if missing_msgs:
            raise HTTPException(
                400,
                f"Cannot mark {code} as completed — "
                f"prerequisite(s) not yet completed: {', '.join(missing_msgs)}"
            )
        session.completed_courses.append(code)
        action = "completed"

    result_data = {
        "session_id": session.session_id,
        "action": action,
        "course": code,
        "completed_courses": session.completed_courses,
    }

    if session.major:
        tracker = RequirementTracker(COURSES, MAJOR_REQUIREMENTS)
        session.progress = tracker.compute_progress(session.major, session.completed_courses)
        result_data["progress"] = session.progress

        sched_result, _ = _run_schedule(session)
        result_data["schedule"] = sched_result

    return result_data


@app.get("/api/session/{session_id}")
def get_session_state(session_id: str):
    """Frontend can poll this to resync after any change."""
    session = get_or_create(session_id)
    return session.to_dict()


@app.get("/api/export/pdf/{session_id}")
def export_pdf(session_id: str):
    """Generate a PDF of the current plan. Uses reportlab."""
    session = get_or_create(session_id)
    if not session.current_plan:
        raise HTTPException(400, "No plan generated yet. Generate a schedule first.")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise HTTPException(500, "reportlab not installed. Run: pip install reportlab --break-system-packages")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc = SimpleDocTemplate(tmp.name, pagesize=letter, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#CC0000"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#555555"))
    head_style = ParagraphStyle("Head", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#111111"))

    elements = []
    elements.append(Paragraph("Pathfinder — Degree Plan", title_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Student: {session.student_name or 'N/A'}", sub_style))
    elements.append(Paragraph(f"Major: {MAJOR_REQUIREMENTS.get(session.major,{}).get('name','N/A')}", sub_style))
    elements.append(Paragraph(f"Classification: {session.classification or 'N/A'}", sub_style))
    elements.append(Spacer(1, 6))

    if session.progress:
        cb = session.progress.get("credit_breakdown", {})
        t = cb.get("total", {})
        elements.append(Paragraph(f"Credits: {t.get('done',0)} / {t.get('target',124)} ({session.progress.get('progress_pct',0)}%)", sub_style))
        elements.append(Paragraph(f"Major: {cb.get('major',{}).get('done',0)}/{cb.get('major',{}).get('target',0)} · "
                                  f"Connections: {cb.get('connections',{}).get('done',0)}/{cb.get('connections',{}).get('target',0)} · "
                                  f"Electives: {cb.get('free_electives',{}).get('done',0)}/{cb.get('free_electives',{}).get('target',0)}", sub_style))
    elements.append(Spacer(1, 10))

    if session.completed_courses:
        elements.append(Paragraph("Completed Courses", head_style))
        elements.append(Paragraph(", ".join(session.completed_courses), sub_style))
        elements.append(Spacer(1, 10))

    plan = session.current_plan
    if plan:
        for sem in plan.get("semesters", []):
            elements.append(Paragraph(f"{sem['label']} ({sem['total_credits']} credits)", head_style))
            data = [["Code", "Course", "Credits", "Time"]]
            for c in sem["courses"]:
                data.append([c["code"], c["name"], str(c["credits"]), c.get("time", "TBD")])
            t = Table(data, colWidths=[60, 220, 50, 120])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F8F8")]),
            ]))
            elements.append(t)
            if sem.get("note"):
                elements.append(Paragraph(f"<i>{sem['note']}</i>", sub_style))
            elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 14))
    elements.append(Paragraph("Generated by Pathfinder · Wittenberg University", ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#AAAAAA"))))

    doc.build(elements)
    return FileResponse(tmp.name, media_type="application/pdf",
                        filename=f"Pathfinder_{session.student_name or 'Plan'}.pdf")
