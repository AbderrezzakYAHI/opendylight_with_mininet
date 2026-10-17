#!/usr/bin/env bash
set -euo pipefail

for cmd in python3 mn ovs-vsctl vtysh; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing command: $cmd"
    exit 1
  fi
done

python3 - <<'PY'
import importlib.util
if importlib.util.find_spec("mininet") is None:
    raise SystemExit("Python Mininet module not found")
print("Python Mininet module: OK")
PY

echo "All local dependencies are available."
