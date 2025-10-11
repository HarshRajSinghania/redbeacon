import os
from typing import Dict, Any, List


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    keys: List[str] = params.get("keys") or []
    prefix: str = params.get("prefix") or ""

    result: Dict[str, Any] = {}
    if keys:
        for k in keys:
            result[k] = os.environ.get(k)
    elif prefix:
        for k, v in os.environ.items():
            if k.startswith(prefix):
                result[k] = v
    else:
        # By default, do not dump all env vars; require keys or prefix
        return {"error": "provide 'keys' or 'prefix'"}

    return {"count": len(result), "vars": result}
