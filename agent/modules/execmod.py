import subprocess
import time
from typing import Dict, Any, List

DEFAULT_TIMEOUT = 10  # seconds
MAX_BYTES = 16 * 1024  # 16KB cap for stdout+stderr


def _truncate(b: bytes, max_len: int) -> tuple[str, bool]:
    if len(b) <= max_len:
        return b.decode(errors="replace"), False
    return b[:max_len].decode(errors="replace"), True


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Prototype command execution (no allowlist). SECURITY: to be hardened later.
    Expected payload:
      {
        "cmd": "echo",          # string executable (required if args not provided)
        "args": ["hello"],      # list[str] (optional)
        "timeout": 10            # seconds (optional)
      }
    Returns: { returncode, stdout, stderr, duration_ms, truncated_stdout, truncated_stderr }
    """
    params = params or {}
    cmd = params.get("cmd")
    args: List[str] = params.get("args") or []
    timeout = float(params.get("timeout", DEFAULT_TIMEOUT))

    if not cmd and not args:
        return {"error": "missing 'cmd' or 'args'"}

    # Build argv without shell to avoid injection
    argv: List[str]
    if cmd:
        argv = [str(cmd)] + [str(a) for a in args]
    else:
        # if only args provided, assume args is full command vector
        argv = [str(a) for a in args]

    start = time.time()
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        duration_ms = int((time.time() - start) * 1000)
        # Truncate outputs
        stdout, trunc_out = _truncate(proc.stdout, MAX_BYTES)
        stderr, trunc_err = _truncate(proc.stderr, MAX_BYTES)
        return {
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "truncated_stdout": trunc_out,
            "truncated_stderr": trunc_err,
        }
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.time() - start) * 1000)
        # e.output / e.stderr may be bytes or None
        out_b = e.output or b""
        err_b = e.stderr or b""
        stdout, trunc_out = _truncate(out_b, MAX_BYTES)
        stderr, trunc_err = _truncate(err_b, MAX_BYTES)
        return {
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "timeout": True,
            "truncated_stdout": trunc_out,
            "truncated_stderr": trunc_err,
        }
    except FileNotFoundError:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "error": f"command not found: {argv[0] if argv else ''}",
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {"error": str(e), "duration_ms": duration_ms}
