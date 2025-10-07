import psutil
import time


def run(params: dict | None = None) -> dict:
    interval = 0.5 if not params else float(params.get("interval", 0.5))
    # Take two samples for a smoother CPU percent
    psutil.cpu_percent(interval=None)
    time.sleep(interval)
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/") if hasattr(psutil, "disk_usage") else None
    data = {
        "cpu_percent": cpu,
        "mem_percent": vm.percent,
        "mem_used_mb": int(vm.used / (1024 * 1024)),
        "mem_total_mb": int(vm.total / (1024 * 1024)),
    }
    if disk:
        data.update({
            "disk_used_mb": int(disk.used / (1024 * 1024)),
            "disk_total_mb": int(disk.total / (1024 * 1024)),
            "disk_percent": disk.percent,
        })
    return data
