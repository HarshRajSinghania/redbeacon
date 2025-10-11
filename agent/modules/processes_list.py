import psutil
from typing import Dict, Any, List


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    name_filter = (params.get("name_filter") or "").lower()
    limit = int(params.get("limit", 200))

    results: List[Dict[str, Any]] = []
    for p in psutil.process_iter(attrs=["pid", "name", "cmdline", "username", "cpu_percent", "memory_percent"], ad_value=None):
        try:
            name = (p.info.get("name") or "")
            if name_filter and name_filter not in name.lower():
                continue
            item = {
                "pid": p.info.get("pid"),
                "name": name,
                "username": p.info.get("username"),
                "cpu_percent": p.info.get("cpu_percent"),
                "memory_percent": p.info.get("memory_percent"),
            }
            # Truncate cmdline to keep payload small
            cmdline = p.info.get("cmdline") or []
            if isinstance(cmdline, list):
                cmdline_str = " ".join(cmdline)
                item["cmdline"] = (cmdline_str[:512] + "…") if len(cmdline_str) > 512 else cmdline_str
            results.append(item)
            if len(results) >= limit:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return {"count": len(results), "processes": results}
