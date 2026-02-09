#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v vhs >/dev/null 2>&1; then
  echo "Error: 'vhs' is not installed."
  echo "Install from: https://github.com/charmbracelet/vhs"
  exit 1
fi

vhs docs/demo/demo.tape
echo "Generated: docs/assets/paperpilot-demo.gif"
