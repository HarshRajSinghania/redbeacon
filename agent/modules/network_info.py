import psutil
from typing import Dict, Any, List


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    addrs = psutil.net_if_addrs()
    info: Dict[str, Any] = {"interfaces": []}
    for name, addr_list in addrs.items():
        iface: Dict[str, Any] = {"name": name, "addresses": []}
        for a in addr_list:
            iface["addresses"].append({
                "family": str(a.family),
                "address": a.address,
                "netmask": getattr(a, "netmask", None),
                "broadcast": getattr(a, "broadcast", None),
                "ptp": getattr(a, "ptp", None),
            })
        info["interfaces"].append(iface)
    return info
