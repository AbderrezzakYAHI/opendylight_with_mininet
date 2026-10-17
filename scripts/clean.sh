#!/usr/bin/env bash
set -euo pipefail
sudo mn -c || true
sudo pkill -f '(^|/)zebra.*mininet' 2>/dev/null || true
sudo pkill -f '(^|/)ospfd.*mininet' 2>/dev/null || true
sudo pkill -f '(^|/)bgpd.*mininet' 2>/dev/null || true
echo "Mininet cleanup completed."
