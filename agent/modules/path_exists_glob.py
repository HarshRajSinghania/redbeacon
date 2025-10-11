from pathlib import Path
from typing import Dict, Any, List
import glob
import os


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    pattern = params.get("glob")
    limit = int(params.get("limit", 100))
    if not pattern:
        return {"error": "missing 'glob'"}

    # Expand user (~) and environment variables
    pattern = os.path.expandvars(os.path.expanduser(pattern))

    matches: List[Dict[str, Any]] = []
    try:
        for i, p in enumerate(glob.iglob(pattern, recursive=True)):
            if i >= limit:
                break
            try:
                path = Path(p)
                st = path.stat()
                matches.append({
                    "path": str(path),
                    "is_file": path.is_file(),
                    "is_dir": path.is_dir(),
                    "size": st.st_size if path.is_file() else None,
                    "mtime": int(st.st_mtime),
                })
            except Exception:
                matches.append({"path": str(p), "error": "stat_failed"})
        return {"count": len(matches), "items": matches}
    except Exception as e:
        return {"error": str(e)}
