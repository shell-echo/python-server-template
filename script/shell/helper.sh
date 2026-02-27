#!/bin/bash

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

: "${ROOT:?ROOT is required}"

if [[ ! -f "$ROOT/.env" ]]; then
    echo ".env not found: $ROOT/.env"
    exit 1
fi

source "$ROOT/.env"
: "${PYTHON_VENV_DIRNAME:?PYTHON_VENV_DIRNAME is required in .env}"
PYTHON_VENV_DIR="$ROOT/$PYTHON_VENV_DIRNAME"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; 
NC='\033[0m';
logger() {
	local level="$1"
	case "$level" in
		success) shift; echo -e "${GREEN}$*${NC}" ;;
		warning) shift; echo -e "${YELLOW}$*${NC}" ;;
		error) shift; echo -e "${RED}$*${NC}" ;;
		*) echo -e "${BLUE}$@${NC}" ;;
	esac
}
