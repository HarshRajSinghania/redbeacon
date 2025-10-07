# Requires: Python 3.11+, venv activated, dependencies installed from agent/requirements.txt
$ErrorActionPreference = "Stop"
# Run as a module so package imports work
python -m agent.agent
