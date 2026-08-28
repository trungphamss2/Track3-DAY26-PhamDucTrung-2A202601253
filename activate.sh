#!/usr/bin/env bash

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
activate_script="$project_root/.venv/Scripts/activate"
env_file="$project_root/.env"

if [[ ! -f "$activate_script" ]]; then
    echo "Virtual environment not found: $activate_script" >&2
    return 1 2>/dev/null || exit 1
fi

source "$activate_script"

if [[ -f "$env_file" ]]; then
    set -a
    source "$env_file"
    set +a
fi

export PYTHONUTF8="${PYTHONUTF8:-1}"

# Google ADK reads GOOGLE_API_KEY, while lesson 01 uses GEMINI_API_KEY.
# Reuse the instructor-provided Gemini key when a separate ADK key is absent.
if [[ -z "${GOOGLE_API_KEY:-}" && -n "${GEMINI_API_KEY:-}" ]]; then
    export GOOGLE_API_KEY="$GEMINI_API_KEY"
fi

echo "DAY26 environment activated: $project_root"
echo "Python: $(command -v python)"
