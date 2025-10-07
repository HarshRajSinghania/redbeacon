import json
import time
import uuid
import socket
import platform
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

import requests

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
STATE_PATH = Path(__file__).resolve().parent / "state.json"


class Agent:
    def __init__(self, cfg: Dict[str, Any]):
        self.server_url = cfg.get("server_url", "http://127.0.0.1:8000")
        self.agent_id = cfg.get("agent_id") or f"agent-{uuid.uuid4()}"
        self.hostname = cfg.get("hostname") or socket.gethostname()
        self.os = cfg.get("os") or f"{platform.system()} {platform.release()}"
        self.version = cfg.get("version", "0.1.0")
        self.token = cfg.get("token", "")
        # TLS settings
        self.ca_cert_path: Optional[str] = cfg.get("ca_cert_path") or None
        # pin_sha256 should be hex string of SHA256 over server cert in DER form
        self.pin_sha256: Optional[str] = (cfg.get("pin_sha256") or "").lower() or None

    def save_config(self):
        data = {
            "server_url": self.server_url,
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os": self.os,
            "version": self.version,
            "token": self.token,
            "ca_cert_path": self.ca_cert_path or "",
            "pin_sha256": self.pin_sha256 or "",
        }
        CONFIG_PATH.write_text(json.dumps(data, indent=2))

    def _request(self, method: str, path: str, headers: Dict[str, str] | None = None, payload: Dict[str, Any] | None = None, timeout: float = 20.0):
        url = f"{self.server_url}{path}"
        verify = self.ca_cert_path if self.ca_cert_path else True
        hdrs = headers.copy() if headers else {}
        with requests.Session() as s:
            resp = s.request(method=method.upper(), url=url, json=payload or {}, headers=hdrs, timeout=timeout, verify=verify, stream=True)
            # Raise for HTTP error first
            resp.raise_for_status()
            # Certificate pinning check (optional)
            if self.pin_sha256:
                try:
                    # Get server cert in DER (binary) form from underlying socket
                    # urllib3 exposes the raw socket via resp.raw.connection.sock
                    der_bytes = resp.raw.connection.sock.getpeercert(binary_form=True)
                    digest = hashlib.sha256(der_bytes).hexdigest()
                    if digest.lower() != self.pin_sha256.lower():
                        raise requests.HTTPError(f"Certificate pin mismatch (got {digest}, expected {self.pin_sha256})", response=resp)
                except AttributeError:
                    # If we cannot access the socket, fail closed when pinning is configured
                    raise requests.HTTPError("Unable to access peer certificate for pinning", response=resp)
            # Now consume body
            return resp

    def enroll(self):
        payload = {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os": self.os,
            "version": self.version,
        }
        resp = self._request("POST", "/enroll", payload=payload, timeout=10)
        data = resp.json()
        self.token = data["token"]
        self.save_config()
        print(f"Enrolled as {self.agent_id}")

    def heartbeat(self):
        headers = {"X-Agent-Token": self.token}
        resp = self._request("POST", "/heartbeat", headers=headers, payload={}, timeout=20)
        return resp.json()

    def submit_result(self, task_id: int, status: str, output: Dict[str, Any]):
        headers = {"X-Agent-Token": self.token}
        payload = {"task_id": task_id, "status": status, "output": output}
        resp = self._request("POST", "/results", headers=headers, payload=payload, timeout=20)
        return resp.json()

    def run_task(self, task: Dict[str, Any]):
        task_id = task["id"]
        ttype = task.get("type")
        payload = task.get("payload") or {}
        try:
            if ttype == "inventory":
                from .modules import inventory as mod
                out = mod.run(payload)
            elif ttype == "metrics":
                from .modules import metrics as mod
                out = mod.run(payload)
            elif ttype == "logs":
                from .modules import logs as mod
                out = mod.run(payload)
            elif ttype == "exec":
                from .modules import execmod as mod
                out = mod.run(payload)
            else:
                out = {"error": f"unknown task type: {ttype}"}
                return self.submit_result(task_id, "error", out)
            return self.submit_result(task_id, "ok", out)
        except Exception as e:
            return self.submit_result(task_id, "error", {"error": str(e)})


def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    # default
    return {
        "server_url": "http://127.0.0.1:8000",
        "agent_id": f"agent-{uuid.uuid4()}",
        "hostname": "",
        "os": "",
        "version": "0.1.0",
        "token": "",
    }


def main():
    cfg = load_config()
    agent = Agent(cfg)

    # Enroll if no token
    if not agent.token:
        try:
            agent.enroll()
        except Exception as e:
            print(f"Enroll failed: {e}")
            time.sleep(5)

    backoff = 1
    while True:
        try:
            hb = agent.heartbeat()
            tasks = hb.get("tasks", [])
            if tasks:
                for t in tasks:
                    agent.run_task(t)
                backoff = 1
            else:
                # No tasks, sleep a bit
                time.sleep(2)
                backoff = 1
        except requests.HTTPError as e:
            # Auto re-enroll if our token is invalid (e.g., server DB reset)
            resp = getattr(e, "response", None)
            if resp is not None and resp.status_code == 401:
                print("Auth error (401). Attempting re-enroll...")
                agent.token = ""
                try:
                    agent.enroll()
                    backoff = 1
                    continue
                except Exception as ee:
                    print(f"Re-enroll failed: {ee}")
            print(f"HTTP error: {e}")
            time.sleep(min(backoff, 30))
            backoff *= 2
        except requests.RequestException as e:
            print(f"Network error: {e}")
            time.sleep(min(backoff, 30))
            backoff *= 2
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
