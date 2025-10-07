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

## TLS + certificate pinning (optional)

You can run the server over HTTPS and have the agent verify a specific certificate (pinning).

1) Generate a self-signed certificate (PowerShell example):
```
openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.crt -days 365 -subj "/CN=127.0.0.1"
```

2) Run the server with TLS:
```
uvicorn server.main:app --host 127.0.0.1 --port 8443 --ssl-keyfile server.key --ssl-certfile server.crt
```

3) Compute the SHA256 pin of the certificate:
```
openssl x509 -in server.crt -noout -fingerprint -sha256
# Or in pure DER digest:
openssl x509 -in server.crt -outform der | openssl dgst -sha256
```
Use the hex digest (without spaces/colons) as `pin_sha256`.

4) Configure the agent `agent/config.json`:
```
{
  "server_url": "https://127.0.0.1:8443",
  "agent_id": "agent-001",
  ...,
  "ca_cert_path": "C:/path/to/server.crt",  // use full path
  "pin_sha256": "<hex_sha256_of_cert_der>"
}
```

5) Run the agent. It will verify the certificate using the CA file and enforce the SHA256 pin.


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
