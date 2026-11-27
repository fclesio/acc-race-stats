# Shortcuts for macOS and Linux; each one calls run.sh, which works without make too.
# Works with GNU make (including 3.81, the one of macOS) and BSD make. On Windows, make.bat does the same.
#   make ARGS='--league "My League"'

SHELL = /bin/sh
ARGS =

.PHONY: run en pt-br demo test check shortcut help

run:  ## ask everything step by step (Portuguese by default)
	@sh ./run.sh $(ARGS)

en:  ## questions and charts in English
	@sh ./run.sh en $(ARGS)

pt-br:  ## questions and charts in Portuguese
	@sh ./run.sh pt-br $(ARGS)

demo:  ## invented race weekend, no server needed
	@sh ./run.sh demo $(ARGS)

test:  ## pytest
	@sh ./run.sh test $(ARGS)

check:  ## ruff and mypy
	@sh ./run.sh check

shortcut:  ## Linux: add ACC Race Stats to the applications menu
	@sh ./run.sh shortcut

help:
	@grep -E '^[a-z-]+:.*## ' Makefile | sed 's/:.*## /\t/'
