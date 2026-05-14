"""tracker.py — Fixed credit model. Separates major/connections/elective credits.
Fixes the 112/100 display bug by tracking each bucket independently.
"""
from typing import List, Dict, Set


class RequirementTracker:
    def __init__(self, courses: Dict, requirements: Dict):
        self.C = courses
        self.R = requirements

    def compute_progress(self, major: str, completed: List[str]) -> Dict:
        req = self.R[major]
        done = set(completed)

        # ── Connections (gen ed) ──
        conn_required = req["core_connections"]
        conn_done = [c for c in conn_required if c in done]
        conn_remain = [c for c in conn_required if c not in done]
        conn_cr_done = sum(self.C.get(c,{}).get("credits",0) for c in conn_done)
        conn_cr_target = req["connections_credits"]

        # ── Major required ──
        maj_required = list(req["major_required"])
        # Add one from each choice group
        for grp in req.get("major_choice_groups", []):
            satisfied = [o for o in grp["options"] if o in done]
            if satisfied:
                maj_required.append(satisfied[0])
            else:
                maj_required.append(grp["options"][0])
        maj_done = [c for c in maj_required if c in done]
        maj_remain = [c for c in maj_required if c not in done]

        # Major electives
        ele = req.get("major_electives", {})
        ele_options = ele.get("options", [])
        ele_count_needed = ele.get("count", 0)
        ele_done_codes = [c for c in ele_options if c in done]
        ele_still_needed = max(0, ele_count_needed - len(ele_done_codes))
        # Pick placeholders for remaining electives
        ele_remain_codes = [c for c in ele_options if c not in done][:ele_still_needed]

        maj_cr_done = sum(self.C.get(c,{}).get("credits",0) for c in maj_done) + \
                      sum(self.C.get(c,{}).get("credits",0) for c in ele_done_codes)
        maj_cr_target = req["major_credits"]

        # ── Free electives (to reach 126 total) ──
        all_categorized = set(conn_required + maj_required + ele_done_codes + ele_remain_codes)
        free_ele_done = [c for c in completed if c not in all_categorized]
        free_cr = sum(self.C.get(c,{}).get("credits",0) for c in free_ele_done)
        free_cr_target = req["total_credits"] - maj_cr_target - conn_cr_target

        total_done = conn_cr_done + maj_cr_done + free_cr
        total_target = req["total_credits"]

        # ── Prereq gaps ──
        all_remain = conn_remain + maj_remain + ele_remain_codes
        gaps = []
        for code in all_remain:
            info = self.C.get(code, {})
            missing = [p for p in info.get("prereqs", []) if p not in done]
            any_list = info.get("prereqs_any", [])
            any_ok = not any_list or any(p in done for p in any_list)
            if not any_ok:
                missing.append(f"one of: {', '.join(any_list)}")
            if missing:
                gaps.append({"course": code, "course_name": info.get("name", code),
                             "missing_prereqs": missing})

        def prereqs_satisfied(c):
            info = self.C.get(c, {})
            all_met = all(p in done for p in info.get("prereqs", []))
            any_list = info.get("prereqs_any", [])
            any_ok = not any_list or any(p in done for p in any_list)
            return all_met and any_ok

        avail_now = [c for c in all_remain if prereqs_satisfied(c)]

        pct = round(min(total_done / total_target * 100, 100.0), 1)
        if pct >= 90: summary = "Almost there — final stretch!"
        elif pct >= 60: summary = f"Good progress — {total_target - total_done} credits remaining."
        elif pct >= 30: summary = f"Solid start — {total_target - total_done} credits ahead."
        else: summary = f"Early journey — {total_target - total_done} credits to go."

        def detail(c):
            return {"code":c,"name":self.C.get(c,{}).get("name",c),"credits":self.C.get(c,{}).get("credits",0),"type":self.C.get(c,{}).get("type","?")}

        return {
            "major": req["name"],
            "credit_breakdown": {
                "major":       {"done": maj_cr_done,  "target": maj_cr_target},
                "connections":  {"done": conn_cr_done, "target": conn_cr_target},
                "free_electives": {"done": free_cr,    "target": max(0, free_cr_target)},
                "total":        {"done": total_done,   "target": total_target},
            },
            "progress_pct": pct,
            "completed_courses": [detail(c) for c in (conn_done + maj_done + ele_done_codes + free_ele_done)],
            "remaining_courses": [detail(c) for c in all_remain],
            "available_now":     [detail(c) for c in avail_now],
            "prerequisite_gaps": gaps,
            "electives_still_needed": ele_still_needed,
            "graduation_summary": summary,
        }
