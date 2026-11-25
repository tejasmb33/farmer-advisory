#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
FARMWISE_PYTHON=""
for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[:2] in ((3, 11), (3, 12)) else 1)' 2>/dev/null; then
        FARMWISE_PYTHON="$candidate"
        break
    fi
done
if [ -z "$FARMWISE_PYTHON" ]; then
    echo 'Install Python 3.12 from https://www.python.org/downloads/macos/ and reopen Terminal.'
    exit 1
fi
if [ ! -d .venv ]; then
    "$FARMWISE_PYTHON" -m venv .venv
fi
if [ ! -x .venv/bin/python ]; then
    echo 'The existing .venv is unusable. Rename it and run this launcher again.'
    exit 1
fi
if [ ! -f .venv/.farmwise-ready ]; then
    .venv/bin/python -m pip install -r requirements.txt
    touch .venv/.farmwise-ready
fi
exec .venv/bin/python -m streamlit run app.py
