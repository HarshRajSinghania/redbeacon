import psutil
import socket
from typing import Dict, Any, List, Optional


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    List open/listening ports.
    Payload:
      { "protocols": ["tcp","udp"], "listening_only": true, "limit": 200 }
    """
    params = params or {}
    want_protocols = set([p.lower() for p in params.get("protocols", ["tcp", "udp"])])
    listening_only = bool(params.get("listening_only", True))
    limit = int(params.get("limit", 200))

    results: List[Dict[str, Any]] = []

    # psutil kinds: 'inet' covers tcp/udp IPv4/6
    for c in psutil.net_connections(kind='inet'):
        try:
            laddr = getattr(c, 'laddr', None)
            raddr = getattr(c, 'raddr', None)
            status = getattr(c, 'status', '')
            pid = getattr(c, 'pid', None)
            family = str(getattr(c, 'family', ''))
            type_ = getattr(c, 'type', None)

            proto: Optional[str] = None
            if type_ == socket.SOCK_STREAM:
                proto = 'tcp'
            elif type_ == socket.SOCK_DGRAM:
                proto = 'udp'
            else:
                proto = 'unknown'

            if proto not in want_protocols:
                continue

            if listening_only and proto == 'tcp' and status and status.lower() != 'listening':
                continue

            item: Dict[str, Any] = {
                'proto': proto,
                'status': status,
                'laddr': f"{getattr(laddr, 'ip', '')}:{getattr(laddr, 'port', '')}" if laddr else None,
                'raddr': f"{getattr(raddr, 'ip', '')}:{getattr(raddr, 'port', '')}" if raddr else None,
                'pid': pid,
            }
            # Try to get process name
            if pid:
                try:
                    p = psutil.Process(pid)
                    item['process'] = p.name()
                except Exception:
                    item['process'] = None
            results.append(item)
            if len(results) >= limit:
                break
        except Exception:
            continue

    return {"count": len(results), "connections": results}
