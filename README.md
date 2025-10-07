# RedBeacon C2 (FastAPI + SQLite + Python Agent)

A minimal, easy-to-understand endpoint management demo:
- Single FastAPI server with SQLite (no Docker, no brokers).
- Simple Python agent that enrolls, heartbeats, pulls tasks, and uploads results.
- Shared-secret auth; optional HTTPS.

## Quick Start

### Prerequisites
- Windows or Linux with Python 3.11+
- Recommended: create a virtual environment

### Install server deps
```
python -m venv .venv
. .venv/Scripts/Activate.ps1  # Windows PowerShell
pip install -r server/requirements.txt
```

### Run server
```
# Option A: use helper script
./run_server.ps1

# Option B: run as module
python -m server.main
```
Server listens on http://127.0.0.1:8000 by default. Open http://127.0.0.1:8000/docs for Swagger.

### Configure and run agent
- Edit `agent/config.json` (server URL and agent name).
```
pip install -r agent/requirements.txt
# Option A: use helper script
./run_agent.ps1

# Option B: run as module
python -m agent.agent
```

## Exec prototype (optional)

This prototype lets the agent run commands remotely via a new task type `exec`.

- Disabled controls: no allowlist yet (you will add it later). Use only in a trusted lab.
- Safety in place: no shell execution, default timeout 10s, output capped to 16KB.

Example task payloads (create via Swagger `POST /tasks`, header `X-Admin-Token: changeme-admin`):

- Windows PowerShell (use `cmd /c`):
```
{
  "target_agent_id": "agent-001",
  "type": "exec",
  "payload": { "cmd": "cmd", "args": ["/c", "echo", "hello"] }
}
```

- Linux/macOS:
```
{
  "target_agent_id": "agent-001",
  "type": "exec",
  "payload": { "cmd": "echo", "args": ["hello"] }
}
```

Result will include: `returncode`, `stdout`, `stderr`, `duration_ms`, and truncation flags.


### Create a task (from Swagger or curl)
- Open http://127.0.0.1:8000/docs
- Use `POST /tasks` with admin token (default: `changeme-admin` in `server/config.py`).
- Example payload to ask an agent to send inventory:
```
{
  "target_agent_id": "<AGENT_ID>",
  "type": "inventory",
  "payload": {}
}
```

The agent will poll tasks on heartbeat and post results.

## Layout
- `server/` FastAPI app and SQLite models
- `agent/` Python agent and simple modules
- `README.md` this file
- `.gitignore`

## Configuration
- `server/config.py` holds admin token and DB path.
- Each agent gets its own token on enrollment. Agents authenticate with header `X-Agent-Token`.

## Security notes
- This is a minimal demo. For production:
  - Use HTTPS (TLS certs) and rotate tokens.
  - Add RBAC and better auditing.

## License
MIT
