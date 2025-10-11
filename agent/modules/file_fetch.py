from pathlib import Path
from typing import Dict, Any
import base64


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    path = params.get("path")
    max_kb = int(params.get("max_kb", 256))
    if not path:
        return {"error": "missing 'path'"}
    p = Path(path)
    if not p.exists() or not p.is_file():
        return {"error": f"file not found: {p}"}
    try:
        data = p.read_bytes()
        cap = max_kb * 1024
        truncated = False
        if len(data) > cap:
            data = data[:cap]
            truncated = True
        b64 = base64.b64encode(data).decode()
        return {
            "path": str(p),
            "size": p.stat().st_size,
            "data_b64": b64,
            "truncated": truncated,
            "max_kb": max_kb,
        }
    except Exception as e:
        return {"error": str(e), "path": str(p)}
