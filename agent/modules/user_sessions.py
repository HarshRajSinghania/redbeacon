import psutil
from typing import Dict, Any, List
from datetime import datetime


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    sessions: List[Dict[str, Any]] = []
    for u in psutil.users():
        sessions.append({
            "name": u.name,
            "terminal": getattr(u, "terminal", None),
            "host": getattr(u, "host", None),
            "started": int(getattr(u, "started", 0) or 0),
        })
    return {"count": len(sessions), "sessions": sessions}
