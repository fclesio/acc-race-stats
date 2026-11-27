#!/bin/sh
# macOS: double-click this file. It opens the Terminal and asks everything step by step.
# macOS: clique duas vezes neste arquivo. Ele abre o Terminal e pergunta tudo passo a passo.
cd -- "$(dirname -- "$0")" || exit 1
sh ./run.sh "$@"
code=$?
echo
printf 'Press Enter to close. / Aperte Enter para fechar. '
read -r _ || true
exit $code
