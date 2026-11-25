# macOS and Linux. On Windows, make.bat does the same.
export PATH := $(HOME)/.local/bin:$(PATH)
ARGS ?=

.DEFAULT_GOAL := run
.PHONY: run en pt-br demo test check setup

run: setup  ## ask everything step by step
	@uv run --quiet --no-dev acc-race-stats $(ARGS)

en: setup  ## charts in English
	@uv run --quiet --no-dev acc-race-stats --lang en $(ARGS)

pt-br: setup  ## charts in Portuguese
	@uv run --quiet --no-dev acc-race-stats --lang pt-br $(ARGS)

demo: setup  ## invented race weekend, no server needed
	@uv run --quiet --no-dev acc-race-stats --demo --session all $(ARGS)

test: setup
	@uv run --quiet pytest

check: setup
	@uv run --quiet ruff check .
	@uv run --quiet mypy

setup:
	@command -v uv >/dev/null 2>&1 || { \
		echo "First run: installing what is needed, only once..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; }
