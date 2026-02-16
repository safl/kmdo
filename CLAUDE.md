# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**kmdo** is a command-line tool that auto-generates command-line usage examples by executing `.cmd` files and capturing their output into `.out` files. It produces YAML (default) or JSONL formatted results to stdout. No external dependencies — stdlib only.

## Build, Test & Install

```bash
make              # clean + build (sdist via python3 -m build)
make all          # clean + uninstall + build + install (via pipx)
make install      # pipx install dist/*.tar.gz
make test         # python3 -m pytest
make format       # ruff format + ruff check --fix on src/ and tests/
make lint         # ruff check on src/ and tests/
make bump         # bump patch version in __init__.py
make release      # clean + build + upload to PyPI
```

Run a single test:
```bash
python3 -m pytest tests/test_cli.py::TestCmdFromFile::test_reads_commands -v
```

## Code Quality

- **Linter/Formatter:** ruff (line-length 88, isort rules)
- **Pre-commit:** ruff + trailing-whitespace/end-of-file/yaml hooks (`.pre-commit-config.yaml`)
- **Testing:** pytest (tests in `tests/`, configured in `pyproject.toml`)
- **Python:** >=3.10, tested against 3.10-3.13

## Architecture

The entire implementation lives in `src/kmdo/cli.py`, structured as a pipeline:

1. **`parse_args()`** — argparse CLI: positional `path`, flags `-r`/`--recursive`, `-s`/`--shell`, `-x`/`--exclude`, `-f`/`--output-format` (yaml/jsonl), `-n`/`--dry-run`, `-t`/`--timeout`
2. **`produce_cmd_output(args)`** — generator that walks the directory tree (via `Path.rglob`) for `.cmd` files, executes each command, writes `.out`/`.err` files, and yields per-command result tuples
3. **`cmd_from_file(fpath)`** — parses `.cmd` files, merging `\` line continuations; empty files use the filename (minus extensions) as the command
4. **`cmd_run(cmd, args)`** — executes via `subprocess.Popen` with configurable shell and optional timeout
5. **`main()`** — entry point that registers signal handlers, streams results (YAML or JSONL), and returns error count as exit code

**CLI flags:**
- `-r`/`--recursive` — only process top-level `.cmd` files
- `-s`/`--shell` — custom shell executable
- `-x`/`--exclude` — skip `.cmd` files matching pattern
- `-f`/`--output-format` — `yaml` (default, streamed) or `jsonl` (streamed, one JSON object per line)
- `-n`/`--dry-run` — list commands without executing
- `-t`/`--timeout` — per-command timeout in seconds

**Special file conventions:**
- `.cmd` → input commands; `.out` → captured output; `.err` → output on error
- `.uone.cmd` → "update on error" variant: writes `.out` even if commands fail

**Entry point:** `kmdo = kmdo.cli:main` (console_scripts in `pyproject.toml`)

**Version:** single `__version__` string in `src/kmdo/__init__.py`

## CI/CD

GitHub Actions workflow (`.github/workflows/selftest.yml`):
- **build_and_check:** matrix of Ubuntu 22.04/24.04 + macOS × Python 3.10-3.13
- **test:** pytest with coverage on Ubuntu across Python 3.10-3.13
- **publish:** PyPI trusted publisher on version tags
