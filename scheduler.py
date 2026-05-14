"""scheduler.py — Fixes:
  1. Credit minimum: 12 is always the floor for full-time/athlete; internship semesters
     don't exempt from it; only explicit part-time request allows under-12; remaining
     credit count < 12 also exempts gracefully with a notice.
  2. Time preferences: avoid_before/avoid_after are HARD constraints on the NEXT semester.
     If a course can't satisfy them, it's placed anyway with a notice (not silently violated).
     prefers_morning / prefers_light_fridays remain soft preferences affecting sort order.
  3. Upcoming vs future semesters: semester index 0 = upcoming; gets real meeting times
     plus all time preferences enforced. Semesters 1+ are future; they get "TBD" times and
     time preferences are not applied. This prevents 8am slots from appearing 3 years out.
"""
from __future__ import annotations
from typing import List, Dict, Set, Optional, Tuple
import re


# ── TIME PARSING ─────────────────────────────────────────────────────────────
def parse_time_slot(slot: str) -> List[Tuple[int, int, int]]:
    """Parse 'MWF 9:00-9:50am' → [(day_idx, start_min, end_min), ...]"""
    if not slot or "Arranged" in slot or slot == "TBD":
        return []
    m = re.match(r"([MTWHF]+)\s+(\d+):(\d+)\s*-\s*(\d+):(\d+)\s*(am|pm)?", slot.strip())
    if not m:
        return []
    days, sh, sm, eh, em, ampm = m.groups()
    sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
    if eh < sh:
        eh += 12
    if ampm == "pm" and sh < 12:
        sh += 12
        if eh < 12:
            eh += 12
    s_min = sh * 60 + sm
    e_min = eh * 60 + em
    DAY = {"M": 0, "T": 1, "W": 2, "H": 3, "F": 4}
    return [(DAY[d], s_min, e_min) for d in days if d in DAY]


def times_conflict(t1: list, t2: list) -> bool:
    for d1, s1, e1 in t1:
        for d2, s2, e2 in t2:
            if d1 == d2 and not (e1 <= s2 or e2 <= s1):
                return True
    return False


def slot_violates_hard_prefs(blocks: list, prefs: dict) -> bool:
    """Return True if ANY meeting in this slot violates a hard time constraint."""
    avoid_before = prefs.get("avoid_before")   # int minutes, e.g. 540 = 9am
    avoid_after  = prefs.get("avoid_after")    # int minutes, e.g. 1020 = 5pm
    for _, start, end in blocks:
        if avoid_before is not None and start < avoid_before:
            return True
        if avoid_after is not None and end > avoid_after:
            return True
    return False


# ── ENGINE ───────────────────────────────────────────────────────────────────
class SchedulingEngine:
    YEAR = {"freshman": 1, "sophomore": 2, "junior": 3, "senior": 4}
    GLOBAL_MIN = 12  # absolute floor for full-time/athlete students

    def __init__(self, courses: Dict, requirements: Dict):
        self.C = courses
        self.R = requirements
        self._tc = {
            code: [parse_time_slot(t) for t in info.get("times", [])]
            for code, info in courses.items()
        }

    # ── REMAINING COURSE RESOLUTION ──────────────────────────────────────────
    def resolve_required(self, major: str, completed_set: Set[str]) -> List[str]:
        req = self.R[major]
        exclude = set(completed_set)
        needed = []

        for c in req["core_connections"]:
            if c not in exclude:
                needed.append(c)

        for c in req["major_required"]:
            if c not in exclude:
                needed.append(c)

        for grp in req.get("major_choice_groups", []):
            if not any(o in completed_set for o in grp["options"]):
                chosen = grp["options"][0]
                for opt in grp["options"]:
                    if opt not in exclude and all(
                        p in completed_set
                        for p in self.C.get(opt, {}).get("prereqs", [])
                    ):
                        chosen = opt
                        break
                if chosen not in exclude:
                    needed.append(chosen)

        ele = req.get("major_electives", {})
        if ele:
            done_e = sum(1 for o in ele["options"] if o in completed_set)
            to_add = max(0, ele["count"] - done_e)
            avail = [o for o in ele["options"] if o not in exclude]
            avail.sort(key=lambda c: len(self.C.get(c, {}).get("prereqs", [])))
            needed.extend(avail[:to_add])

        return needed

    # ── FILLER POOL ───────────────────────────────────────────────────────────
    def _build_filler_pool(self, major: str, completed_set: Set[str],
                           already_planned: Set[str]) -> List[str]:
        """Return all catalog courses that:
          - are NOT already completed or planned
          - have prereqs that could be met (we check per-semester later)
          - are type elective or core
          - are NOT capstone/senior seminar
        Ordered by course number (lower = easier/earlier).
        Used to pad semesters below the credit minimum.
        """
        exclude = completed_set | already_planned
        pool = []
        for code, info in self.C.items():
            if code in exclude:
                continue
            num = re.search(r"\d+$", code)
            if num and int(num.group()) >= 400:
                continue  # skip senior/capstone courses for filler
            if info.get("type") in ("elective", "core"):
                pool.append(code)
        # Sort: fewer prereqs first, then by course number
        pool.sort(key=lambda c: (
            len(self.C.get(c, {}).get("prereqs", [])),
            int(re.search(r"\d+$", c).group()) if re.search(r"\d+$", c) else 999
        ))
        return pool

    # ── PREREQ CHECK ─────────────────────────────────────────────────────────
    def _prereqs_met(self, code: str, done: Set[str]) -> bool:
        """Check if all prerequisites are satisfied.
        Supports both:
          prereqs: [A, B]        — ALL of A and B required
          prereqs_any: [C, D]    — at least ONE of C or D required
        """
        info = self.C.get(code, {})
        # All-required prereqs
        for p in info.get("prereqs", []):
            if p not in done:
                return False
        # OR-prereqs: at least one must be satisfied
        any_list = info.get("prereqs_any", [])
        if any_list and not any(p in done for p in any_list):
            return False
        return True

    # ── TIME SLOT PICKING ────────────────────────────────────────────────────
    def _pick_time(
        self,
        code: str,
        used_blocks: list,
        prefs: dict,
        warnings: list,
        is_upcoming: bool,
    ) -> Tuple[str, list]:
        """
        Pick a meeting time for a course.
        - is_upcoming=True:  apply all preferences (hard + soft); generate notices for violations
        - is_upcoming=False: return "TBD" — future semesters don't get real times
        """
        if not is_upcoming:
            return ("TBD", [])

        times = self.C.get(code, {}).get("times", [])
        blocks_list = self._tc.get(code, [])
        if not times:
            return ("TBD", [])

        cands = list(zip(times, blocks_list if blocks_list else [[] for _ in times]))

        # ── Separate candidates: hard-constraint-compliant vs violating ──────
        hard_ok   = [(t, b) for t, b in cands if not slot_violates_hard_prefs(b, prefs)]
        hard_fail = [(t, b) for t, b in cands if     slot_violates_hard_prefs(b, prefs)]

        # ── Sort by soft preferences within each bucket ───────────────────────
        def soft_score(entry: Tuple[str, list]) -> int:
            t, b = entry
            s = 0
            if prefs.get("prefers_morning") and b and all(x[1] < 720 for x in b):
                s -= 10
            if prefs.get("prefers_light_fridays") and b and any(x[0] == 4 for x in b):
                s += 10
            return s

        hard_ok.sort(key=soft_score)
        hard_fail.sort(key=soft_score)

        # ── Try hard-ok slots first ────────────────────────────────────────────
        for t, b in hard_ok:
            if not any(times_conflict(b, u) for u in used_blocks):
                return (t, b)

        # ── Fall back to hard-fail slots with notice ───────────────────────────
        if hard_fail:
            avoid_before = prefs.get("avoid_before")
            violation_reason = ""
            if avoid_before is not None:
                avoid_h = avoid_before // 60
                avoid_m = avoid_before % 60
                violation_reason = (
                    f"No section of {code} ({self.C[code]['name']}) is available "
                    f"after {avoid_h}:{avoid_m:02d}am — using earliest available section. "
                    f"This course has no alternative time slots that satisfy your preference."
                )
            for t, b in hard_fail:
                if not any(times_conflict(b, u) for u in used_blocks):
                    if violation_reason:
                        warnings.append(violation_reason)
                    return (t, b)

        # ── Last resort: any slot even with time conflict ─────────────────────
        all_cands = hard_ok + hard_fail
        if all_cands:
            warnings.append(f"Time conflict could not be fully resolved for {code}")
            return all_cands[0]

        return ("TBD", [])

    # ── BUILD ONE SEMESTER ────────────────────────────────────────────────────
    def _build_semester(
        self,
        remaining: list,
        done: Set[str],
        max_cr: int,
        effective_min: int,
        prefs: dict,
        year: int,
        term: str,
        capstone_codes: Set[str],
        warnings: list,
        is_upcoming: bool,
        total_remaining_credits: int,
        filler_pool: list,
    ) -> dict:
        """
        Build one semester.
        - is_upcoming: True only for semester index 0; applies time prefs + hard constraints
        - total_remaining_credits: total credits left to schedule; used to determine if
          falling below effective_min is justified (end-of-degree scenario)
        """
        avail = [
            c for c in remaining
            if self._prereqs_met(c, done)
            and term in self.C.get(c, {}).get("offered", [])
        ]
        caps     = [c for c in avail if c in capstone_codes]
        non_caps = [c for c in avail if c not in capstone_codes]
        non_caps.sort(key=lambda c: (
            {"core": 0, "major": 1, "elective": 2}.get(
                self.C.get(c, {}).get("type", "elective"), 3),
            len(self.C.get(c, {}).get("prereqs", []))
        ))

        chosen, total, used_blocks = [], 0, []

        for code in non_caps:
            cr = self.C[code]["credits"]
            if total + cr > max_cr:
                continue
            t, b = self._pick_time(code, used_blocks, prefs, warnings, is_upcoming)
            used_blocks.append(b)
            total += cr
            chosen.append({
                "code": code,
                "name": self.C[code]["name"],
                "credits": cr,
                "type": self.C[code]["type"],
                "time": t,
                "is_upcoming": is_upcoming,
                "core_protected": self.C[code].get("core_protected", False),
                "explanation": "",
            })

        # Add capstone only when all non-capstone courses are placed
        placed = {c["code"] for c in chosen}
        rem_non_cap = [c for c in remaining if c not in placed and c not in capstone_codes]
        if not rem_non_cap and caps:
            for cap_code in caps:
                if self._prereqs_met(cap_code, done | placed):
                    cr = self.C[cap_code]["credits"]
                    if total + cr <= max_cr + 2:
                        t, b = self._pick_time(cap_code, used_blocks, prefs, warnings, is_upcoming)
                        chosen.append({
                            "code": cap_code,
                            "name": self.C[cap_code]["name"],
                            "credits": cr,
                            "type": self.C[cap_code]["type"],
                            "time": t,
                            "is_upcoming": is_upcoming,
                            "core_protected": True,
                            "explanation": "",
                        })
                        total += cr

        # ── PAD TO MINIMUM using filler electives ─────────────────────────────
        # After placing required courses, if we're under effective_min, pull
        # eligible filler courses from the broader catalog to reach 12 credits.
        if filler_pool and effective_min > 0 and total < effective_min:
            placed = {c["code"] for c in chosen}
            for filler_code in filler_pool:
                if total >= effective_min:
                    break
                if filler_code in placed:
                    continue
                if not self._prereqs_met(filler_code, done | placed):
                    continue
                if term not in self.C.get(filler_code, {}).get("offered", []):
                    continue
                cr = self.C[filler_code]["credits"]
                if total + cr > max_cr:
                    continue
                t, b = self._pick_time(filler_code, used_blocks, prefs, warnings, is_upcoming)
                used_blocks.append(b)
                total += cr
                placed.add(filler_code)
                chosen.append({
                    "code": filler_code,
                    "name": self.C[filler_code]["name"],
                    "credits": cr,
                    "type": self.C[filler_code].get("type", "elective"),
                    "time": t,
                    "is_upcoming": is_upcoming,
                    "core_protected": False,
                    "explanation": "Added to meet the 12-credit full-time minimum.",
                })

        # ── Minimum credit notice (reads FINAL total after capstone) ─────────
        if chosen and total < effective_min and effective_min > 0:
            # Justify if this is genuinely the end of the degree
            total_remaining = sum(self.C.get(c, {}).get("credits", 0) for c in remaining)
            if total_remaining <= effective_min:
                # Not a problem — student is in their final partial semester
                pass
            else:
                warnings.append(
                    f"Year {year} {term}: {total} credits scheduled "
                    f"(full-time minimum is {effective_min}). "
                    f"Reason: limited course availability this term due to prerequisites "
                    f"or offering schedules — not related to internship status."
                )

        # Semester note
        has_cap = any(
            c["code"].endswith("490") or c["code"].endswith("400")
            for c in chosen
        )
        has_internship = any("381" in c["code"] or "internship" in c["name"].lower()
                             for c in chosen)
        if has_cap:
            note = "Capstone semester — present strong."
        elif has_internship and is_upcoming:
            note = "Internship semester — 12-credit minimum still applies; internship credits count toward total."
        elif year == 1 and term == "Fall":
            note = "First semester — build strong habits."
        elif total >= 17:
            note = "Heavy load — plan your week carefully."
        elif 0 < total <= 12:
            note = "Light load — good for internships or research."
        else:
            note = "Balanced semester."

        if is_upcoming:
            note += " (Upcoming — real meeting times shown.)"
        elif chosen:
            note += " (Future — meeting times assigned closer to enrollment.)"

        return {
            "label": f"Year {year} — {term}",
            "year": year,
            "term": term,
            "courses": chosen,
            "total_credits": total,
            "note": note,
            "is_upcoming": is_upcoming,
        }

    # ── BUILD FULL PLAN ───────────────────────────────────────────────────────
    def _build_plan(
        self,
        remaining: list,
        completed: list,
        max_cr: int,
        effective_min: int,
        prefs: dict,
        start_year: int,
        capstone_codes: Set[str],
        warnings: list,
        major: str,
    ) -> list:
        terms = ["Fall", "Spring"]
        sems = []
        cur_done = set(completed)
        rem = list(remaining)
        year = start_year
        tidx = 0
        stall = 0
        sem_index = 0

        for _ in range(16):
            if not rem:
                break
            term = terms[tidx % 2]
            is_upcoming = (sem_index == 0)
            total_rem_cr = sum(self.C.get(c, {}).get("credits", 0) for c in rem)

            # Build filler pool fresh each semester — excludes anything placed so far
            all_planned = {c["code"] for s in sems for c in s["courses"]}
            filler = self._build_filler_pool(major, cur_done, set(rem) | all_planned)

            sem = self._build_semester(
                rem, cur_done, max_cr, effective_min,
                prefs, year, term, capstone_codes, warnings,
                is_upcoming=is_upcoming,
                total_remaining_credits=total_rem_cr,
                filler_pool=filler,
            )
            if not sem["courses"]:
                tidx += 1
                if tidx % 2 == 0:
                    year += 1
                stall += 1
                if stall > 4:
                    warnings.append(f"Could not schedule: {', '.join(rem)}")
                    break
                continue

            stall = 0
            sem_index += 1
            placed = {c["code"] for c in sem["courses"]}
            rem = [c for c in rem if c not in placed]
            cur_done |= placed
            sems.append(sem)
            tidx += 1
            if tidx % 2 == 0:
                year += 1

        return sems

    # ── SCORING ───────────────────────────────────────────────────────────────
    def _score(self, sems: list, prefs: dict, strategy_label: str) -> dict:
        n = len(sems)
        if n == 0:
            return {"graduation_speed": 0, "workload_balance": 0,
                    "preference_fit": 0, "total": 0}

        cps = [s["total_credits"] for s in sems]
        avg = sum(cps) / n
        variance = sum((c - avg) ** 2 for c in cps) / n
        max_sem = max(cps)

        speed = min(100, max(0, 100 - (n - 8) * 10))

        if strategy_label == "Balanced":
            balance = min(100, max(0, 100 - variance * 4))
        elif strategy_label == "Accelerated":
            balance = min(100, max(0, 100 - variance * 1.5))
        else:
            heavy_penalty = max(0, max_sem - 14) * 8
            balance = min(100, max(0, 100 - heavy_penalty))

        # Preference fit: only score the UPCOMING semester's actual times
        fit = 100
        upcoming_sems = [s for s in sems if s.get("is_upcoming")]
        check_sems = upcoming_sems if upcoming_sems else sems[:1]
        for s in check_sems:
            for c in s["courses"]:
                times = self.C.get(c["code"], {}).get("times", [])
                for t in times:
                    blks = parse_time_slot(t)
                    if prefs.get("prefers_light_fridays") and blks and any(b[0] == 4 for b in blks):
                        fit -= 5
                    avoid_before = prefs.get("avoid_before")
                    if avoid_before and blks and any(b[1] < avoid_before for b in blks):
                        fit -= 8

        fit = min(100, max(0, fit))

        if strategy_label == "Balanced":
            total = speed * 0.3 + balance * 0.5 + fit * 0.2
        elif strategy_label == "Accelerated":
            total = speed * 0.6 + balance * 0.2 + fit * 0.2
        else:
            total = speed * 0.2 + balance * 0.6 + fit * 0.2

        return {
            "graduation_speed": round(speed, 1),
            "workload_balance": round(balance, 1),
            "preference_fit": round(fit, 1),
            "total": round(min(100, max(0, total)), 1),
        }

    # ── MAIN ENTRY ────────────────────────────────────────────────────────────
    def generate(
        self,
        major: str,
        completed: list,
        classification: str,
        max_credits: int = 16,
        min_credits: int = 12,
        prefers_morning: bool = False,
        prefers_light_fridays: bool = False,
        avoid_before: Optional[int] = None,
        avoid_after: Optional[int] = None,
    ) -> dict:
        req = self.R[major]
        completed_set = set(completed)
        start = self.YEAR.get(classification, 1)
        prefs = {
            "prefers_morning": prefers_morning,
            "prefers_light_fridays": prefers_light_fridays,
            "avoid_before": avoid_before,   # hard constraint: no slots starting before this minute
            "avoid_after": avoid_after,     # hard constraint: no slots ending after this minute
        }

        capstone_codes = set()
        for c in req["major_required"]:
            num = re.search(r"\d+$", c)
            if num and int(num.group()) >= 400:
                capstone_codes.add(c)
        # Also include capstone alternatives from choice groups (e.g. DATA491, DATA499)
        for grp in req.get("major_choice_groups", []):
            for opt in grp["options"]:
                num = re.search(r"\d+$", opt)
                if num and int(num.group()) >= 490:
                    capstone_codes.add(opt)
        # And any in the remaining that look like capstones (4xx or ends 490/491/499)
        for c in req.get("major_electives", {}).get("options", []):
            num = re.search(r"\d+$", c)
            if num and int(num.group()) >= 490:
                capstone_codes.add(c)

        # Minimum credit floor — internship semesters do NOT exempt from this
        global_min = max(self.GLOBAL_MIN, min_credits) if min_credits > 0 else 0

        strategies = [
            {
                "label": "Balanced",
                "max": max_credits,
                "min": global_min,
                "desc": f"~{max_credits} credits/semester, even distribution",
            },
            {
                "label": "Accelerated",
                "max": min(18, max_credits + 2),
                "min": global_min,
                "desc": f"Up to {min(18, max_credits+2)} credits early, graduate sooner",
            },
            {
                "label": "Lighter Load",
                "max": max(global_min, max_credits - 4),
                "min": global_min,   # 12-credit minimum applies to all plans for full-time students
                "desc": f"~{max(global_min, max_credits-4)} credits/semester, relaxed pace",
            },
        ]

        done_cr = sum(self.C.get(c, {}).get("credits", 0) for c in completed)
        alternatives = []

        for strat in strategies:
            warnings: list = []
            remaining = self.resolve_required(major, completed_set)
            sems = self._build_plan(
                remaining, completed_set,
                strat["max"], strat["min"],
                prefs, start, capstone_codes, warnings,
                major=major,
            )
            sc = self._score(sems, prefs, strat["label"])
            sched_cr = sum(s["total_credits"] for s in sems)

            alternatives.append({
                "label": strat["label"],
                "description": strat["desc"],
                "score": sc,
                "total_semesters": len(sems),
                "total_credits": sched_cr + done_cr,
                "scheduled_credits": sched_cr,
                "completed_credits": done_cr,
                "semesters": sems,
                "warnings": warnings,
            })

        alternatives.sort(key=lambda a: -a["score"]["total"])
        return {
            "major": req["name"],
            "best": alternatives[0],
            "alternatives": alternatives,
        }
