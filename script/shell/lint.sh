#!/bin/bash

set -euo pipefail
source script/shell/helper.sh

MODE="${1:-check}"

if [[ "$MODE" != "check" && "$MODE" != "modify" ]]; then
    logger error "Invalid mode: $MODE"
    logger "Usage: $0 [check|modify]"
    exit 1
fi

logger "Static type check..."
if [[ ! -d "$PYTHON_VENV_DIR" ]]; then
    logger error "venv not found: $PYTHON_VENV_DIR"
    logger "Run: bash script/shell/env.sh init"
    exit 1
fi

logger "\nActivate venv..."
source "$PYTHON_VENV_DIR/bin/activate"
python -m pyright "$ROOT"

run () {
    local tool="$1"
    local args=("${@:2}")
    local base_args=("${args[@]:0:${#args[@]}-1}")
    local root_dir="${args[-1]}"
    local check_flag="--check"

    if [[ "$tool" == "isort" ]]; then
        check_flag="--check-only"
    fi
    
    logger "\nRunning $tool (mode:$MODE)..."
    if [[ $MODE == "check" ]]; then
        if ! python -m "$tool" "$check_flag" "${base_args[@]}" "$root_dir"; then
            logger error "Error: $tool found issues."
            exit 1
        fi
    else
        python -m "$tool" "${base_args[@]}" "$root_dir"
    fi
}

run "autoflake" --expand-star-imports \
    --remove-all-unused-imports --remove-unused-variables --remove-rhs-for-unused-variables \
    --in-place --recursive --exclude="$PYTHON_VENV_DIRNAME" \
    "$ROOT"

run "isort" --skip="$PYTHON_VENV_DIRNAME" "$ROOT"

run "black" -v "$ROOT"


logger "\n--- Tool Version ---"
logger success "Autoflake: $(autoflake --version | head -n1 | awk '{print $2}')"
logger success "Isort: $(isort --version | grep VERSION | awk '{print $2}')"
logger success "Black: $(black --version | head -n1 | awk '{print $2}')"
