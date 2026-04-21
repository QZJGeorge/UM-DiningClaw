#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
LOCK_DIR="${XDG_RUNTIME_DIR:-/tmp}"
LOCK_FILE="${LOCK_DIR}/diningclaw-publish.lock"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-diningclaw}"

log() {
  printf '[publish] %s\n' "$*"
}

find_conda_python() {
  local candidate=""
  local conda_bin=""
  local conda_base=""

  if [[ -n "${DININGCLAW_PYTHON:-}" ]]; then
    candidate="${DININGCLAW_PYTHON}"
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
    log "DININGCLAW_PYTHON is set but not executable: ${candidate}"
  fi

  if [[ -n "${CONDA_PREFIX:-}" ]]; then
    candidate="${CONDA_PREFIX}/bin/python"
    if [[ -x "${candidate}" && "$(basename "${CONDA_PREFIX}")" == "${CONDA_ENV_NAME}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  fi

  for candidate in \
    "${HOME}/anaconda3/envs/${CONDA_ENV_NAME}/bin/python" \
    "${HOME}/miniconda3/envs/${CONDA_ENV_NAME}/bin/python"; do
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  if [[ -n "${CONDA_EXE:-}" && -x "${CONDA_EXE}" ]]; then
    conda_bin="${CONDA_EXE}"
  elif command -v conda >/dev/null 2>&1; then
    conda_bin="$(command -v conda)"
  fi

  if [[ -n "${conda_bin}" ]]; then
    conda_base="$(dirname "$(dirname "${conda_bin}")")"
    candidate="${conda_base}/envs/${CONDA_ENV_NAME}/bin/python"
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  fi

  return 1
}

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  log "Another publish run is already in progress; exiting."
  exit 0
fi

if [[ -f .env ]]; then
  # Load local secrets without exporting unrelated shell variables.
  set -a
  source .env
  set +a
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY is not set."
  exit 1
fi

if ! PYTHON_BIN="$(find_conda_python)"; then
  if ! PYTHON_BIN="$(command -v python3)"; then
    log "Unable to find Python or Conda environment '${CONDA_ENV_NAME}'."
    exit 1
  fi
  log "Conda environment '${CONDA_ENV_NAME}' not found; falling back to ${PYTHON_BIN}."
fi

log "Running pipeline with ${PYTHON_BIN}"
"${PYTHON_BIN}" main.py

git add -A docs/
if git diff --cached --quiet; then
  log "No changes to commit."
  exit 0
fi

commit_date="$(TZ=America/Detroit date +%Y-%m-%d)"
git commit -m "Update ${commit_date}"
git push origin main
