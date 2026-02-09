#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

print_banner() {
  local title="$1"
  printf '\n\033[1;36m== %s ==\033[0m\n' "$title"
}

run() {
  printf '\n$ %s\n' "$*"
  "$@"
}

print_banner "PaperPilot Demo (Safe / No Write)"
echo "This script only runs non-destructive commands."
echo "Use it for terminal demos, onboarding, and quick sanity checks."

print_banner "Environment"
run python --version

print_banner "Core Pipeline Help"
run python scripts/langchain_pipeline.py --help

print_banner "Shell Pipeline Help"
run bash scripts/ai_toolbox_pipeline.sh --help

print_banner "Watch Import Help"
run python scripts/watch_and_import_papers.py --help

print_banner "Done"
echo "Demo completed."
