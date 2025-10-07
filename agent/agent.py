import json
import time
import uuid
import socket
import platform
from pathlib import Path
from typing import Dict, Any

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

    def save_config(self):
        data = {
            "server_url": self.server_url,
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os": self.os,
            "version": self.version,
            "token": self.token,
        }
        CONFIG_PATH.write_text(json.dumps(data, indent=2))

    def enroll(self):
        url = f"{self.server_url}/enroll"
        payload = {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os": self.os,
            "version": self.version,
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self.token = data["token"]
        self.save_config()
        print(f"Enrolled as {self.agent_id}")

    def heartbeat(self):
        url = f"{self.server_url}/heartbeat"
        headers = {"X-Agent-Token": self.token}
        resp = requests.post(url, json={}, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def submit_result(self, task_id: int, status: str, output: Dict[str, Any]):
        url = f"{self.server_url}/results"
        headers = {"X-Agent-Token": self.token}
        payload = {"task_id": task_id, "status": status, "output": output}
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
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
        except requests.RequestException as e:
            print(f"Network error: {e}")
            time.sleep(min(backoff, 30))
            backoff *= 2
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
