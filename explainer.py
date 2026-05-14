"""explainer.py — Course explanation module."""
from typing import List, Dict

class ExplanationModule:
    def __init__(self, courses, requirements):
        self.C = courses; self.R = requirements

    def explain_course(self, code, major, completed, preferences):
        c = self.C.get(code, {}); req = self.R.get(major, {}); done = set(completed)
        parts = []
        if code in req.get("major_required", []):
            parts.append(f"{code} is required for your {req.get('name',major)} major")
        elif code in req.get("core_connections", []):
            parts.append(f"{code} satisfies a Connections Curriculum requirement")
            if c.get("core_protected"):
                parts.append("this course is mandatory and cannot be removed")
        else:
            in_group = False
            for grp in req.get("major_choice_groups", []):
                if code in grp["options"]:
                    parts.append(f"{code} fulfills the {grp['label']} requirement"); in_group = True; break
            if not in_group:
                if code in req.get("major_electives",{}).get("options",[]):
                    parts.append(f"{code} counts toward your major elective requirement")
                else:
                    parts.append(f"{code} is a free elective toward your 126-credit graduation total")
        prereqs = c.get("prereqs", [])
        if prereqs:
            sat = [p for p in prereqs if p in done]
            if sat:
                names = ", ".join(self.C.get(p,{}).get("name",p) for p in sat)
                parts.append(f"prerequisite{'s' if len(sat)>1 else ''} ({names}) completed")
        else:
            parts.append("no prerequisites needed")
        if preferences.get("prefers_morning") and any("8:" in t or "9:" in t or "10:" in t for t in c.get("times",[])):
            parts.append("morning section available")
        if preferences.get("prefers_light_fridays") and not any("F" in t.split()[0] for t in c.get("times",[]) if len(t.split())>0):
            parts.append("no Friday meetings")
        sentence = ", ".join(parts)
        return sentence[0].upper() + sentence[1:] + "."
