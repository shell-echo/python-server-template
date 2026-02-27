#!/bin/bash

set -euo pipefail
source script/shell/helper.sh

library_packages() {
    grep -v '^[[:space:]]*#' "$ROOT/library.txt" | awk -F ':' '{gsub(/^[ \t]+|[ \t]+$/, "", $1); if ($1 != "") print $1}'
}

install_library_packages() {
    local packages=()
    mapfile -t packages < <(library_packages)

    if [[ ${#packages[@]} -eq 0 ]]; then
        logger error "No packages found in $ROOT/library.txt"
        exit 1
    fi

    logger "Library: ${packages[*]}"
    pip install "${packages[@]}" -i "$PYTHON_PIP_INDEX_URL"
}

reset() {
    "$PYTHON_BIN" -c "import sys; print(sys.version);"

    if [[ -z "${PYTHON_VENV_DIR:-}" || "$PYTHON_VENV_DIR" == "/" ]]; then
        logger error "Unsafe PYTHON_VENV_DIR: ${PYTHON_VENV_DIR:-<empty>}"
        exit 1
    fi

    rm -rf -- "$PYTHON_VENV_DIR"
    "$PYTHON_BIN" -m venv "$PYTHON_VENV_DIR"

    source "$PYTHON_VENV_DIR/bin/activate"
    python -m pip install --upgrade pip
}

init() {
    reset

    local dep_file="$ROOT/$PYTHON_DEPENDENT_FILENAME"
    if [[ -f "$dep_file" ]]; then
        pip install -r "$dep_file" -i "$PYTHON_PIP_INDEX_URL"
    else
        logger warning "$PYTHON_DEPENDENT_FILENAME not found, installing packages from library.txt"
        install_library_packages
    fi

    pip list

    logger success "Init env success 🎉."
}

freeze() {
    "$PYTHON_BIN" -c "import sys; print(sys.version);"
    source "$PYTHON_VENV_DIR/bin/activate"
    pip freeze > "$ROOT/$PYTHON_DEPENDENT_FILENAME"
}

library() {
    reset

    install_library_packages
    pip list

    logger success "library success 🎉."
}

install_vscode_extension() {
	local extension="$1"
	
	if ! code --list-extensions | grep -qx "$extension"; then
		logger "$extension installing..."
		if ! code --install-extension "$extension" --force >/dev/null 2>&1; then
			logger error "$extension installation failed!"
			return 1
		fi
	fi

	version=$(code --list-extensions --show-versions | grep -E "^$extension@" | awk -F'@' '{print $2}')
	logger success "\033[32m$extension version: $version\033[0m"
}

vscode() {
    EXTS="ms-python.black-formatter ms-python.isort ms-python.python ms-python.vscode-pylance"

    for ext in $EXTS; do
        install_vscode_extension "$ext"
    done
}

help() {
    logger "Usage: $0 {init|freeze|library|vscode}"
}

bashrc() {
    BASHRC="$HOME/.bashrc"
    LINE="[ -f \"$ROOT/.env\" ] && set -a && . \"$ROOT/.env\" && set +a"

    if ! grep -Fxq "$LINE" "$BASHRC"; then
        echo "$LINE" >> "$BASHRC"
    fi
}

CMD="${1:-help}"

case "$CMD" in
    init)
        init
        ;;
    freeze)
        freeze
        ;;
    library)
        library
        ;;
    vscode)
        vscode
        ;;
    bashrc)
        bashrc
        ;;
    ""|help|-h|--help)
        help
        ;;
    *)
        logger warning "Unknown command: $CMD"
        help
        ;;
esac
