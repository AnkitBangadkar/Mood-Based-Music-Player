#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR="venv"
MARKER="$VENV_DIR/.installed"

msg() { echo "▶ $1"; }

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        echo "Error: Python not found. Please install Python 3.9+"
        exit 1
    fi
}

setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        msg "Creating virtual environment..."
        "$PYTHON" -m venv "$VENV_DIR"
    fi
}

install_deps() {
    if [ ! -f "$MARKER" ]; then
        msg "Installing dependencies..."
        source "$VENV_DIR/bin/activate"
        if command -v uv &> /dev/null; then
            uv pip install -r requirements.txt -q 2>/dev/null || \
            pip install -r requirements.txt -q
        else
            pip install -r requirements.txt -q
        fi
        touch "$MARKER"
    fi
}

main() {
    check_python
    setup_venv
    source "$VENV_DIR/bin/activate"
    install_deps
    msg "Starting server..."
    python main.py
}

main "$@"
