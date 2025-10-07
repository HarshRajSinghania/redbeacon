# Requires: Python 3.11+, venv activated, dependencies installed from server/requirements.txt
$ErrorActionPreference = "Stop"
# Run as a module so relative imports (from .db, etc.) work
python -m server.main
