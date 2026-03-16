#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pkill -f "$SCRIPT_DIR/dashboard.py" >/dev/null 2>&1 || true
nohup /usr/bin/env python3 "$SCRIPT_DIR/dashboard.py" >/tmp/image-gen-dashboard.log 2>&1 &
