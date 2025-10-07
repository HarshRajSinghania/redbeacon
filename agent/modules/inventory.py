import platform
import socket
import psutil


def run(params: dict | None = None) -> dict:
    uname = platform.uname()
    info = {
        "hostname": socket.gethostname(),
        "os": f"{uname.system} {uname.release}",
        "kernel": uname.version,
        "machine": uname.machine,
        "cpu_count": psutil.cpu_count(logical=True),
        "memory_total_mb": int(psutil.virtual_memory().total / (1024 * 1024)),
        "disks": [],
        "net_ifaces": list(psutil.net_if_addrs().keys()),
        "process_count": len(psutil.pids()),
    }
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            info["disks"].append({
                "device": part.device,
                "mount": part.mountpoint,
                "fstype": part.fstype,
                "total_mb": int(usage.total / (1024 * 1024)),
                "used_mb": int(usage.used / (1024 * 1024)),
            })
        except Exception:
            continue
    return info
