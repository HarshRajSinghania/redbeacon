from pathlib import Path
from typing import Dict, Any
import hashlib

ALLOWED_ALGOS = {"md5", "sha1", "sha256", "sha512"}


def _hash_file(p: Path, algo: str, max_bytes: int) -> Dict[str, Any]:
    h = hashlib.new(algo)
    total = 0
    with p.open("rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                # Only hash up to max_bytes
                over = total - max_bytes
                if over > 0:
                    keep = len(chunk) - over
                    if keep > 0:
                        h.update(chunk[:keep])
                return {"digest": h.hexdigest(), "bytes_hashed": max_bytes, "truncated": True}
            h.update(chunk)
    return {"digest": h.hexdigest(), "bytes_hashed": total, "truncated": False}


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    path = params.get("path")
    if not path:
        return {"error": "missing 'path'"}
    algo = str(params.get("algo", "sha256")).lower()
    if algo not in ALLOWED_ALGOS:
        return {"error": f"unsupported algo: {algo}", "allowed": sorted(list(ALLOWED_ALGOS))}
    max_mb = float(params.get("max_mb", 10))
    max_bytes = int(max_mb * 1024 * 1024)

    p = Path(path)
    if not p.exists() or not p.is_file():
        return {"error": f"file not found: {p}"}
    try:
        res = _hash_file(p, algo, max_bytes)
        res.update({"algo": algo, "path": str(p), "size": p.stat().st_size})
        return res
    except Exception as e:
        return {"error": str(e), "path": str(p)}
