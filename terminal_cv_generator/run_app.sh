#!/bin/bash
# Use Hermes agent venv so rich/run_agent/AIAgent are available
PYTHON="/home/qba/.hermes/hermes-agent/venv/bin/python"
cd /home/qba/jobhunter/terminal_cv_generator
"$PYTHON" app.py