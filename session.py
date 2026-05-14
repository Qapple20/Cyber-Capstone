"""session.py — In-memory session store. Single source of truth.

Every component (scheduler, chatbot, tracker, frontend) reads/writes
through this module. No stale copies. No desync.

For a capstone, in-memory dict is the right choice:
- Firebase adds complexity without benefit for a single-user demo
- SQLite would be overkill for session-level state
- This is simple, debuggable, and fast

Production upgrade path: swap the dict for Redis or Firebase Realtime DB.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid
import copy


@dataclass
class StudentSession:
    """Everything we know about the current student. Updated in-place."""
    # Identity
    session_id: str = ""
    student_name: str = ""
    major: str = ""
    classification: str = ""
    is_athlete: bool = False
    is_full_time: bool = True
    is_part_time: bool = False  # explicit opt-in; only this lowers credit min below 12

    # Academic state
    completed_courses: List[str] = field(default_factory=list)
    locked_courses: List[str] = field(default_factory=list)

    # Current plan
    current_plan: Optional[Dict] = None
    all_alternatives: List[Dict] = field(default_factory=list)
    active_alt_index: int = 0

    # Chatbot memory
    chat_history: List[Dict] = field(default_factory=list)
    asked_questions: List[str] = field(default_factory=list)

    # Preferences — richer model
    known_preferences: Dict[str, Any] = field(default_factory=dict)
    # Known keys:
    #   max_credits: int         — target ceiling per semester
    #   prefers_morning: bool    — prefer morning slots (soft preference)
    #   prefers_light_fridays: bool — avoid Friday meetings
    #   avoid_before: int|None   — hard constraint: no classes starting before N minutes
    #                              e.g. avoid_before=540 means no 8am (9:00am = 540)
    #   avoid_after: int|None    — no classes starting after N minutes (e.g. 1020 = 5pm)

    # Progress cache
    progress: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "student_name": self.student_name,
            "major": self.major,
            "classification": self.classification,
            "is_athlete": self.is_athlete,
            "is_full_time": self.is_full_time,
            "is_part_time": self.is_part_time,
            "completed_courses": self.completed_courses,
            "locked_courses": self.locked_courses,
            "current_plan": self.current_plan,
            "all_alternatives": self.all_alternatives,
            "active_alt_index": self.active_alt_index,
            "chat_history": self.chat_history[-20:],
            "asked_questions": self.asked_questions,
            "known_preferences": self.known_preferences,
            "progress": self.progress,
        }

    def max_credits(self) -> int:
        return self.known_preferences.get("max_credits", 16)

    def min_credits(self) -> int:
        """
        12-credit minimum for full-time students and athletes — always.
        Internship semesters do NOT reduce this; the internship course itself
        counts toward the semester credits.
        The only exceptions:
          1. Student explicitly requested part-time status
          2. Fewer than 12 credits remain before graduation (handled in scheduler)
        """
        if self.is_part_time:
            return 0   # student explicitly opted out of full-time minimum
        if self.is_athlete or self.is_full_time:
            return 12
        return 0


# ─── GLOBAL SESSION STORE ────────────────────────────────────────────────────
_sessions: Dict[str, StudentSession] = {}


def get_session(session_id: str) -> Optional[StudentSession]:
    return _sessions.get(session_id)


def create_session() -> StudentSession:
    sid = str(uuid.uuid4())[:8]
    s = StudentSession(session_id=sid)
    _sessions[sid] = s
    return s


def get_or_create(session_id: Optional[str]) -> StudentSession:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    return create_session()


def update_session(session_id: str, **kwargs) -> StudentSession:
    s = _sessions.get(session_id)
    if not s:
        s = create_session()
    for k, v in kwargs.items():
        if hasattr(s, k):
            setattr(s, k, v)
    return s
