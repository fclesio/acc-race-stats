#!/bin/sh
# Launcher for macOS and Linux. Needs only /bin/sh and curl (or wget): no make, no Python.
#   ./run.sh                 asks everything step by step
#   ./run.sh demo | en | pt-br
#   ./run.sh --league "My League" ...   any option of acc-race-stats
#   ./run.sh test | check    for developers
#   ./run.sh shortcut        Linux: adds ACC Race Stats to the applications menu (the first run does it too)
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$here"
if [ ! -f pyproject.toml ]; then
    echo "Unzip the whole project folder first, then open this file from there." >&2
    echo "Descompacte a pasta inteira do projeto primeiro e abra este arquivo de lá." >&2
    exit 1
fi
# uv goes to a known folder and the shell profile is not touched: the installer then prints no
# "add it to your PATH, restart your shell" instructions that a user would think they must follow
UV_INSTALL_DIR="$HOME/.local/bin"
PATH="$UV_INSTALL_DIR:$HOME/.cargo/bin:$PATH"
export PATH

install_uv() {
    command -v uv >/dev/null 2>&1 && return 0
    echo "First run: installing what is needed, only once. Nothing else to do. / Primeira vez: instalando o necessário, só uma vez. Não precisa fazer nada."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$UV_INSTALL_DIR" UV_NO_MODIFY_PATH=1 sh -s -- --quiet
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$UV_INSTALL_DIR" UV_NO_MODIFY_PATH=1 sh -s -- --quiet
    else
        echo "Install curl and run again. / Instale o curl e rode de novo." >&2
        exit 1
    fi
    command -v uv >/dev/null 2>&1 || {
        echo "The installation did not work. Check the internet connection and try again." >&2
        echo "A instalação não funcionou. Verifique a internet e tente de novo." >&2
        exit 1
    }
}

shortcut() {
    folder="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$folder"
    cat >"$folder/acc-race-stats.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=ACC Race Stats
Comment=Charts from Assetto Corsa Competizione server results
Exec=sh "$here/run.sh"
Path=$here
Terminal=true
Categories=Game;Utility;
DESKTOP
    echo "Added to the applications menu: $folder/acc-race-stats.desktop"
}

case "${1:-}" in
shortcut) shortcut; exit 0 ;;
esac
# Linux: after the first run the program is in the applications menu, without typing anything
if [ "$(uname -s)" = Linux ] && [ ! -f "${XDG_DATA_HOME:-$HOME/.local/share}/applications/acc-race-stats.desktop" ]; then
    shortcut >/dev/null 2>&1 || true
fi
install_uv
[ -d .venv ] || echo "Preparing, only the first time: it can take a few minutes... / Preparando, só na primeira vez: pode levar alguns minutos..."
case "${1:-}" in
demo) shift; exec uv run --quiet --no-dev acc-race-stats --demo --session all "$@" ;;
en | pt-br) lang=$1; shift; exec uv run --quiet --no-dev acc-race-stats --lang "$lang" "$@" ;;
test) shift; exec uv run --quiet pytest "$@" ;;
check) uv run --quiet ruff check . && uv run --quiet ruff format --check . && exec uv run --quiet mypy ;;
*) exec uv run --quiet --no-dev acc-race-stats "$@" ;;
esac
