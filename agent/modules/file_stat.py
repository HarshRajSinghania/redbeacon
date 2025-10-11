from pathlib import Path
from typing import Dict, Any
import os
import stat
import time


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    path = params.get("path")
    if not path:
        return {"error": "missing 'path'"}
    p = Path(path)
    info: Dict[str, Any] = {"path": str(p)}
    if not p.exists():
        info.update({"exists": False})
        return info

    try:
        s = p.stat()
        info.update({
            "exists": True,
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "size": s.st_size,
            "mode": stat.S_IMODE(s.st_mode),
            "mtime": int(s.st_mtime),
            "ctime": int(s.st_ctime),
            "atime": int(s.st_atime),
        })
        return info
    except Exception as e:
        return {"error": str(e), "path": str(p)}
