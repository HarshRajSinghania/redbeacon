import psutil
import time
from typing import Dict, Any


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    boot_time = psutil.boot_time()
    now = time.time()
    return {
        "boot_time": int(boot_time),
        "uptime_seconds": int(now - boot_time),
    }
