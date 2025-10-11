import psutil
from typing import Dict, Any, List


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    parts = psutil.disk_partitions(all=False)
    mounts: List[Dict[str, Any]] = []
    for p in parts:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            mounts.append({
                "device": p.device,
                "mount": p.mountpoint,
                "fstype": p.fstype,
                "total_mb": int(usage.total / (1024 * 1024)),
                "used_mb": int(usage.used / (1024 * 1024)),
                "free_mb": int(usage.free / (1024 * 1024)),
                "percent": usage.percent,
            })
        except Exception:
            # Skip inaccessible mounts
            continue
    return {"count": len(mounts), "mounts": mounts}
