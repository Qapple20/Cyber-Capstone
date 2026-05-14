"""chatbot.py — Rewritten to fix:
  1. Lighter load now respects user's immediate credit request, then applies lighter strategy
  2. Chatbot validates prerequisites before marking a course completed
  3. All three plans are explained with their tradeoffs in the response
  4. Credit minimum logic is clearly communicated when requests can't be honored
  5. No direct session.completed_courses mutation without prereq check
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple
from session import StudentSession


# ── INTENT RECOGNITION ──────────────────────────────────────────
INTENTS = {
    "generate": [
        r"\b(build|create|generate|make|plan|schedule)\b.*\b(schedule|plan|degree)\b",
        r"\bI('m| am)?\s+(a\s+)?(freshman|sophomore|junior|senior)\b",
        r"\bstart\s+(fresh|over)\b",
    ],
    "modify_friday":    [r"\blight(er)?\s+friday", r"\bno.*friday", r"\bavoid\s+friday"],
    "modify_morning":   [r"\bmorning\s+class", r"\bearly\s+class"],
    "avoid_early":      [r"\bno\s+8\s*am", r"\bno\s+early", r"\bavoid\s+8",
                         r"\bno\s+class\w*\s+before\s+\d",
                         r"\bnothing\s+before\s+\d",
                         r"\bno\s+classes?\s+before"],
    "set_part_time":    [r"\bpart[- ]time", r"\bpart\s+time"],
    "modify_accelerate":[r"\bgraduate\s+(early|sooner|faster)", r"\baccelerate",
                         r"\bfinish\s+(faster|sooner|early)"],
    "modify_lighten":   [r"\blighten", r"\bless\s+credits?", r"\blighter"],
    "set_credits":      [r"\b(\d{1,2})\s*credits?\s*(per\s+semester|each|minimum|min|next)",
                         r"\bminimum\s+(\d{1,2})\s*credits?",
                         r"\bbump\s+.*(\d{1,2})\s*credits?"],
    "compare":    [r"\bcompare", r"\balternative", r"\bother\s+option", r"\bwhich\s+plan"],
    "explain":    [r"\bwhy\s+(did|does|is)", r"\bexplain", r"\bhow\s+(does|is)"],
    "remove_course": [r"\b(remove|drop|skip|take out)\s+([A-Z]{2,5}\d{3})"],
    "add_course":    [r"\b(add|include|put)\s+([A-Z]{2,5}\d{3})"],
    "progress":   [r"\bhow\s+(am I|far|close)", r"\bprogress",
                   r"\bcredits?\s+(left|remaining|done)"],
    "export":     [r"\b(export|pdf|download|print)\b"],
    "greeting":   [r"\b(hi|hello|hey|what'?s up)\b"],
    "name_given": [r"\b(my name is|call me)\s+(\w+)"],
    "athlete":    [r"\b(athlete|play|sport|team)\b"],
    "mark_completed": [
        r"\b(completed?|done with|took|passed|finished)\s+[A-Z]{2,5}\d{3}",
        r"\b[A-Z]{2,5}\d{3}\s+(is\s+)?(completed?|done|passed|taken)",
    ],
}


def classify(text: str) -> List[str]:
    t = text.lower()
    matched = []
    for intent, patterns in INTENTS.items():
        for p in patterns:
            if re.search(p, t):
                matched.append(intent)
                break
    return matched or ["generate"]


def extract_major(text: str) -> Optional[str]:
    t = text.lower()
    if re.search(r"\bdata\s*science|\bds\b", t):
        return "data_science"
    if re.search(r"\bfinance|\bfin\b", t):
        return "finance"
    return None


def extract_classification(text: str) -> Optional[str]:
    for c in ["freshman", "sophomore", "junior", "senior"]:
        if c in text.lower():
            return c
    return None


def extract_courses(text: str) -> List[str]:
    """Extract course codes from text, with no fuzzy matching needed here —
    raw extraction only. Fuzzy resolution happens in fuzzy_match_course."""
    return list(set(re.findall(r"\b([A-Z]{2,5}\d{3})\b", text.upper())))


# Canonical prefix aliases — maps common typos/abbreviations to the real prefix
_PREFIX_ALIASES: Dict[str, str] = {
    # Accounting typos
    "ACT":  "ACCT",
    "ACNT": "ACCT",
    "ACC":  "ACCT",
    # Business typos
    "BSN":  "BUSN",
    "BUS":  "BUSN",
    "BSNS": "BUSN",
    # Computer science typos
    "CMP":  "COMP",
    "COM":  "COMP",
    "CS":   "COMP",
    # Data science typos
    "DAT":  "DATA",
    "DS":   "DATA",
    # Economics typos
    "ECO":  "ECON",
    "ECN":  "ECON",
    # Math typos
    "MTH":  "MATH",
    "MAT":  "MATH",
    # Environmental science
    "ESC":  "ESCI",
    "ENV":  "ESCI",
    # Psychology
    "PSY":  "PSYC",
    # Language
    "LAN":  "LANG",
    # English
    "ENG":  "ENGL",
}


def fuzzy_match_course(raw: str, courses_db: Dict) -> Optional[str]:
    """Try to resolve a raw extracted code (possibly mistyped) to a real catalog code.
    Returns the matched course code if found, else None.
    Strategy:
      1. Exact match (fast path)
      2. Prefix alias substitution  (ACT225 → ACCT225)
      3. Edit-distance-1 on prefix  (single dropped/swapped letter)
      4. Number-only match when prefix is completely missing
    """
    raw = raw.strip().upper()

    # 1. Exact match
    if raw in courses_db:
        return raw

    # Split prefix and number
    m = re.match(r"([A-Z]+)(\d+)$", raw)
    if not m:
        return None
    prefix, number = m.group(1), m.group(2)

    # 2. Alias substitution
    if prefix in _PREFIX_ALIASES:
        candidate = _PREFIX_ALIASES[prefix] + number
        if candidate in courses_db:
            return candidate

    # 3. Try all catalog codes that share the same number
    same_number = [c for c in courses_db if c.endswith(number)]
    if not same_number:
        return None

    # Among same-number candidates, find the one with closest prefix
    def edit_dist(a: str, b: str) -> int:
        """Simple edit distance (insertions/deletions only) between two strings."""
        m, n = len(a), len(b)
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, n + 1):
                temp = dp[j]
                if a[i-1] == b[j-1]:
                    dp[j] = prev
                else:
                    dp[j] = 1 + min(prev, dp[j], dp[j-1])
                prev = temp
        return dp[n]

    best_code, best_dist = None, 999
    for candidate in same_number:
        cand_prefix = re.match(r"([A-Z]+)", candidate).group(1)
        d = edit_dist(prefix, cand_prefix)
        if d < best_dist:
            best_dist = d
            best_code = candidate

    # Only accept if edit distance is small relative to prefix length (≤2 edits)
    if best_dist <= 2:
        return best_code

    return None


def extract_and_resolve_courses(text: str, courses_db: Dict) -> List[Dict]:
    """Extract course codes from text and resolve each to a catalog code.
    Returns list of {raw, resolved, matched} dicts.
    'matched' is True if fuzzy resolution changed the code.
    """
    # Extract anything that looks like a course code (2-5 letters + 3 digits)
    raw_codes = list(set(re.findall(r"\b([A-Z]{2,5}\d{3})\b", text.upper())))
    results = []
    for raw in raw_codes:
        resolved = fuzzy_match_course(raw, courses_db)
        if resolved:
            results.append({
                "raw": raw,
                "resolved": resolved,
                "matched": resolved != raw,
            })
    return results


def extract_name(text: str) -> Optional[str]:
    m = re.search(r"(?:my name is|call me)\s+(\w+)", text, re.I)
    return m.group(1).title() if m else None


def extract_credit_request(text: str) -> Optional[int]:
    """Extract explicit credit numbers from user request."""
    for pat in [
        r"\b(\d{1,2})\s*credits?\s*(?:per\s+semester|each|minimum|min|next)",
        r"\bminimum\s+(\d{1,2})\s*credits?",
        r"\bbump\s+.*?(\d{1,2})\s*credits?",
        r"\b(\d{1,2})\s*cr\b",
    ]:
        m = re.search(pat, text, re.I)
        if m:
            val = int(m.group(1))
            if 8 <= val <= 20:
                return val
    return None


def extract_avoid_before(text: str) -> Optional[int]:
    """Parse 'no 8am', 'nothing before 9', 'no classes before 10am' → minutes since midnight.
    Returns the minimum start time the student will accept.
    e.g. 'no 8am' → 540 (9:00am = the earliest they'll accept)
         'nothing before 9' → 540 (9:00am)
         'nothing before 10' → 600 (10:00am)
    """
    t = text.lower()

    # "no 8am" / "avoid 8am" → don't want anything starting at 8:xx
    m = re.search(r"\bno\s+8\s*(am|:00)?\b|\bavoid\s+8\s*(am|:00)?\b", t)
    if m:
        return 9 * 60   # 9:00am is the earliest allowed

    # "nothing before 9" / "no classes before 10am"
    m = re.search(r"\b(nothing|no\s+class\w*)\s+before\s+(\d{1,2})\s*(am)?", t)
    if m:
        hr = int(m.group(2))
        if hr < 12 and "pm" not in t:
            return hr * 60

    # "no early classes" → treat as no 8am
    if re.search(r"\bno\s+early\s+class", t):
        return 9 * 60

    return None


def validate_prereqs(code: str, completed: List[str], courses_db: Dict) -> Tuple[bool, List[str]]:
    """Returns (ok, missing_desc).
    Handles both prereqs (ALL required) and prereqs_any (ONE required).
    """
    info = courses_db.get(code, {})
    completed_set = set(completed)
    missing = []

    # All-required prereqs
    for p in info.get("prereqs", []):
        if p not in completed_set:
            missing.append(p)

    # OR-prereqs: fail only if NONE satisfied
    any_list = info.get("prereqs_any", [])
    if any_list and not any(p in completed_set for p in any_list):
        missing.append(f"one of: {', '.join(any_list)}")

    return len(missing) == 0, missing


def explain_plans(alternatives: List[Dict], session: StudentSession) -> str:
    """Generate a human-readable explanation of all three plans."""
    if not alternatives:
        return ""
    parts = ["Here are your 3 plan options:\n"]
    for alt in alternatives:
        sc = alt["score"]
        sems = alt["total_semesters"]
        cr = alt["total_credits"]
        label = alt["label"]
        desc = alt.get("description", "")

        if label == "Balanced":
            rationale = (
                f"• **Balanced** — {sems} semesters, {cr} total credits. "
                f"{desc}. "
                f"This plan distributes your courses as evenly as possible. "
                f"Balance score: {sc['workload_balance']}/100, "
                f"Speed: {sc['graduation_speed']}/100. "
                f"Best choice if you want steady, predictable semesters."
            )
        elif label == "Accelerated":
            rationale = (
                f"• **Accelerated** — {sems} semesters, {cr} total credits. "
                f"{desc}. "
                f"This plan front-loads credits so you finish faster, but earlier "
                f"semesters will be heavier. "
                f"Speed score: {sc['graduation_speed']}/100, "
                f"Balance: {sc['workload_balance']}/100. "
                f"Best if graduating early is the priority."
            )
        else:
            rationale = (
                f"• **Lighter Load** — {sems} semesters, {cr} total credits. "
                f"{desc}. "
                f"This plan keeps each semester lighter, which means more semesters overall. "
                f"Balance score: {sc['workload_balance']}/100. "
                f"Best if you're working, an athlete, or want more breathing room."
            )

        if alt.get("warnings"):
            rationale += f" Note: {alt['warnings'][0]}"
        parts.append(rationale)

    parts.append(
        f"\nOverall scores reflect how well each plan fits your preferences "
        f"(graduation speed, workload balance, time preferences)."
    )
    return "\n".join(parts)


# ── MAIN PROCESSOR ──────────────────────────────────────────────
def process_message(
    text: str,
    session: StudentSession,
    courses_db: Dict,
    requirements_db: Dict,
) -> Dict:
    """
    Returns {response_text, should_regenerate, updated_prefs, credit_override}.
    credit_override: if user specified a credit amount, this overrides session prefs.
    """
    intents = classify(text)
    response_parts = []
    should_regenerate = False
    updated_prefs = {}
    credit_override = None

    # ── Identity extraction ──────────────────────────────────────
    name = extract_name(text)
    if name:
        session.student_name = name
        if "name" not in session.asked_questions:
            session.asked_questions.append("name")
            response_parts.append(f"Nice to meet you, {name}!")

    major = extract_major(text)
    if major and major != session.major:
        session.major = major
        if "major" not in session.asked_questions:
            session.asked_questions.append("major")

    cls = extract_classification(text)
    if cls and cls != session.classification:
        session.classification = cls
        if "classification" not in session.asked_questions:
            session.asked_questions.append("classification")

    # ── Explicit credit request (propagates to ALL strategies) ───
    requested_credits = extract_credit_request(text)
    if requested_credits is not None:
        old = session.known_preferences.get("max_credits", 16)
        session.known_preferences["max_credits"] = requested_credits
        credit_override = requested_credits
        updated_prefs["max_credits"] = requested_credits

        min_cr = session.min_credits()
        if requested_credits < min_cr:
            response_parts.append(
                f"I can't go below {min_cr} credits per semester for full-time "
                f"students — setting minimum to {min_cr}."
            )
            session.known_preferences["max_credits"] = min_cr
            credit_override = min_cr
        else:
            response_parts.append(
                f"Setting target to {requested_credits} credits/semester. "
                f"All three plans will use this as the starting point — "
                f"Balanced targets exactly {requested_credits}, "
                f"Accelerated pushes to {min(18, requested_credits+2)}, "
                f"Lighter Load stays around {max(session.min_credits(), requested_credits-4)}."
            )
        should_regenerate = True

    # ── Completed course detection (with fuzzy/alias matching) ──────────────
    resolved_courses = extract_and_resolve_courses(text, courses_db)
    completed_keywords = r"\b(completed?|done|took|taken|passed|finished|have|already|did)\b"
    has_completed_signal = bool(re.search(completed_keywords, text.lower()))
    is_profile_msg = bool(major or cls)
    # Keep a plain list of resolved codes for backward compat
    codes = [r["resolved"] for r in resolved_courses]

    if resolved_courses and (has_completed_signal or is_profile_msg):
        added = []
        fuzzy_confirmations = []
        blocked = []
        for entry in resolved_courses:
            code = entry["resolved"]
            raw = entry["raw"]
            if code in session.completed_courses:
                continue
            # Fuzzy match: tell the user what we mapped it to
            if entry["matched"]:
                fuzzy_confirmations.append(
                    f"I recognized '{raw}' as {code} ({courses_db.get(code,{}).get('name',code)})."
                )
            ok, missing = validate_prereqs(code, session.completed_courses, courses_db)
            if ok:
                session.completed_courses.append(code)
                added.append(code)
            else:
                missing_names = ", ".join(
                    f"{p} ({courses_db.get(p,{}).get('name',p)})" for p in missing
                )
                blocked.append(
                    f"{code} ({courses_db.get(code,{}).get('name',code)}) — "
                    f"needs {missing_names} first"
                )
        if fuzzy_confirmations:
            response_parts.extend(fuzzy_confirmations)
        if added:
            names = [f"{c} ({courses_db.get(c,{}).get('name',c)})" for c in added]
            response_parts.append(f"Marked as completed: {', '.join(names)}.")
            should_regenerate = True
        if blocked:
            response_parts.append(
                f"Could not mark as completed (prerequisites not done): "
                f"{'; '.join(blocked)}."
            )

    # ── Explicit mark_completed intent ───────────────────────────
    if "mark_completed" in intents and resolved_courses and not (has_completed_signal and is_profile_msg):
        for entry in resolved_courses:
            code = entry["resolved"]
            raw = entry["raw"]
            if code not in session.completed_courses:
                if entry["matched"]:
                    response_parts.append(
                        f"I recognized '{raw}' as {code} ({courses_db.get(code,{}).get('name',code)})."
                    )
                ok, missing = validate_prereqs(code, session.completed_courses, courses_db)
                if ok:
                    session.completed_courses.append(code)
                    response_parts.append(
                        f"Marked {code} ({courses_db.get(code,{}).get('name',code)}) as completed."
                    )
                    should_regenerate = True
                else:
                    missing_names = ", ".join(
                        f"{p} ({courses_db.get(p,{}).get('name',p)})" for p in missing
                    )
                    response_parts.append(
                        f"Can't mark {code} as completed — prerequisites not done: "
                        f"{missing_names}. Complete those first."
                    )

    # ── Athlete detection ────────────────────────────────────────
    if "athlete" in intents:
        session.is_athlete = True
        if "athlete" not in session.asked_questions:
            session.asked_questions.append("athlete")
            response_parts.append(
                "Got it — as a student-athlete, I'll enforce a 12-credit "
                "minimum per semester across all plans. Note: this applies even "
                "during internship semesters, since the internship course itself "
                "counts toward your 12 credits."
            )

    # ── Part-time request ────────────────────────────────────────
    if "set_part_time" in intents:
        session.is_part_time = True
        session.is_full_time = False
        if "part_time" not in session.asked_questions:
            session.asked_questions.append("part_time")
            response_parts.append(
                "Switched to part-time mode — the 12-credit minimum no longer applies. "
                "Plans can go below 12 credits per semester."
            )
        should_regenerate = True

    # ── Avoid early/late time constraints ────────────────────────
    if "avoid_early" in intents:
        avoid_min = extract_avoid_before(text)
        if avoid_min is None:
            avoid_min = 9 * 60  # default: no 8am
        old_avoid = session.known_preferences.get("avoid_before")
        session.known_preferences["avoid_before"] = avoid_min
        updated_prefs["avoid_before"] = avoid_min
        h = avoid_min // 60
        m_min = avoid_min % 60
        response_parts.append(
            f"Got it — no classes starting before {h}:{m_min:02d}am. "
            f"This is a hard constraint on your next semester's real time slots. "
            f"If a required course has NO section after that time, I'll schedule it anyway "
            f"and explain why in the notices."
        )
        should_regenerate = True

    # ── Preference modifications ─────────────────────────────────
    if "modify_friday" in intents:
        session.known_preferences["prefers_light_fridays"] = True
        updated_prefs["prefers_light_fridays"] = True
        response_parts.append("Got it — I'll avoid Friday meetings where possible across all plans.")
        should_regenerate = True

    if "modify_morning" in intents:
        session.known_preferences["prefers_morning"] = True
        updated_prefs["prefers_morning"] = True
        response_parts.append("Prioritizing morning sections.")
        should_regenerate = True

    if "modify_accelerate" in intents:
        session.known_preferences["max_credits"] = 18
        updated_prefs["max_credits"] = 18
        response_parts.append(
            "Switching to accelerated mode — targeting up to 18 credits/semester. "
            "Note: capstones are Spring-only, so there's a floor on how fast we can go."
        )
        should_regenerate = True

    if "modify_lighten" in intents and requested_credits is None:
        # Lighten without a specific number — pull back by 4 from current
        current = session.known_preferences.get("max_credits", 16)
        new_max = max(session.min_credits(), current - 4)
        session.known_preferences["max_credits"] = new_max
        updated_prefs["max_credits"] = new_max
        min_note = (
            f" (12-credit minimum still applies since you're full-time)"
            if session.is_full_time else ""
        )
        response_parts.append(
            f"Pulling back to ~{new_max} credits/semester for the lighter plan{min_note}. "
            f"This will add semesters but make each one more manageable."
        )
        should_regenerate = True

    # ── Remove course ────────────────────────────────────────────
    if "remove_course" in intents:
        m = re.search(r"\b(remove|drop|skip|take out)\s+([A-Z]{2,5}\d{3})", text, re.I)
        if m:
            code = m.group(2).upper()
            if courses_db.get(code, {}).get("core_protected", False):
                cname = courses_db.get(code, {}).get("name", code)
                response_parts.append(
                    f"I can't remove {code} ({cname}) — it's a mandatory graduation "
                    f"requirement. Wittenberg requires all Connections and capstone courses."
                )
            else:
                if session.current_plan:
                    for sem in session.current_plan.get("semesters", []):
                        sem["courses"] = [c for c in sem["courses"] if c["code"] != code]
                        sem["total_credits"] = sum(c["credits"] for c in sem["courses"])
                response_parts.append(f"Removed {code} from your active plan.")
                should_regenerate = True

    # ── Progress inquiry ─────────────────────────────────────────
    if "progress" in intents and session.progress:
        p = session.progress
        cb = p.get("credit_breakdown", {})
        t = cb.get("total", {})
        maj = cb.get("major", {})
        conn = cb.get("connections", {})
        response_parts.append(
            f"You've completed {t.get('done',0)}/{t.get('target',124)} credits "
            f"({p.get('progress_pct',0)}%). "
            f"Major: {maj.get('done',0)}/{maj.get('target',0)} credits. "
            f"Connections Curriculum: {conn.get('done',0)}/{conn.get('target',0)} credits. "
            f"{p.get('graduation_summary','')}"
        )
        if p.get("prerequisite_gaps"):
            gap = p["prerequisite_gaps"][0]
            response_parts.append(
                f"Heads up: {gap['course']} ({gap['course_name']}) is blocked — "
                f"still needs {', '.join(gap['missing_prereqs'])}."
            )

    # ── Compare / explain plans ──────────────────────────────────
    if ("compare" in intents or "explain" in intents) and session.all_alternatives:
        response_parts.append(explain_plans(session.all_alternatives, session))

    # ── Export ───────────────────────────────────────────────────
    if "export" in intents:
        response_parts.append(
            "Click the ⬇ PDF button in the schedule view to download your plan "
            "with credit breakdown and advisor notes."
        )

    # ── Generate / regenerate ────────────────────────────────────
    if "generate" in intents or (should_regenerate and not response_parts):
        missing = []
        if not session.major:
            missing.append("your major (Finance or Data Science)")
        if not session.classification:
            missing.append("your class year (freshman/sophomore/junior/senior)")
        if missing:
            response_parts.append(
                f"To build your plan I need: {', '.join(missing)}."
            )
            should_regenerate = False
        elif not response_parts:
            cr = session.known_preferences.get("max_credits", 16)
            response_parts.append(
                f"Building your 3-plan schedule now — targeting {cr} credits/semester "
                f"as the baseline."
            )
            should_regenerate = True

    # ── Greeting ─────────────────────────────────────────────────
    if "greeting" in intents and not response_parts:
        g = session.student_name or "there"
        response_parts.append(
            f"Hey {g}! Tell me your major and year to get started, "
            f"or click a student profile in the sidebar."
        )

    # ── Fallback ──────────────────────────────────────────────
    if not response_parts:
        if session.current_plan:
            response_parts.append(
                "Your plan is loaded. You can ask me to adjust it — for example: "
                "'lighter load', 'no Fridays', 'I want 16 credits next semester', "
                "or 'explain the three options'."
            )
        else:
            response_parts.append(
                "Tell me your major and year, and I'll build your full degree plan."
            )

    session.chat_history.append({"role": "user", "text": text})
    response_text = " ".join(response_parts)
    session.chat_history.append({"role": "ai", "text": response_text})

    return {
        "response_text": response_text,
        "should_regenerate": (
            should_regenerate
            and bool(session.major)
            and bool(session.classification)
        ),
        "updated_prefs": updated_prefs,
        "credit_override": credit_override,
    }
