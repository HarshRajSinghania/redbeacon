from pathlib import Path


def run(params: dict | None = None) -> dict:
    params = params or {}
    path = params.get("path")
    max_lines = int(params.get("max_lines", 200))
    if not path:
        return {"error": "missing 'path'"}
    p = Path(path)
    if not p.exists() or not p.is_file():
        return {"error": f"file not found: {path}"}
    try:
        lines = p.read_text(errors="ignore").splitlines()
        tail = lines[-max_lines:]
        return {"path": str(p), "lines": tail, "line_count": len(tail)}
    except Exception as e:
        return {"error": str(e)}
