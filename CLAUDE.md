# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**kmdo** is a command-line tool that auto-generates command-line usage examples by executing `.cmd` files and capturing their output into `.out` files. It produces YAML-formatted results to stdout. No external dependencies — stdlib only.

## Build, Test & Install

```bash
make              # clean + build (sdist via python3 -m build)
make all          # clean + uninstall + build + install (via pipx)
make install      # pipx install dist/*.tar.gz
make test         # python3 -m pytest
make format       # black + isort on src/ and tests/
make release      # clean + build + upload to PyPI
```

Run a single test:
```bash
python3 -m pytest tests/test_cli.py::TestCmdFromFile::test_reads_commands -v
```

## Code Quality

- **Formatter:** Black (line-length 88)
- **Import sorting:** isort (black profile)
- **Testing:** pytest (tests in `tests/`, configured in `pyproject.toml`)
- **Python:** >=3.10, tested against 3.10-3.13

## Architecture

The entire implementation lives in `src/kmdo/cli.py` (~130 lines), structured as a pipeline:

1. **`parse_args()`** — argparse CLI: positional `path`, flags `-r`/`--recursive`, `-s`/`--shell`, `-x`/`--exclude`
2. **`produce_cmd_output(args)`** — generator that walks the directory tree (via `Path.rglob`) for `.cmd` files, executes each command, writes `.out`/`.err` files, and yields per-command result tuples
3. **`cmd_from_file(fpath)`** — parses `.cmd` files, merging `\` line continuations; empty files use the filename (minus extensions) as the command
4. **`cmd_run(cmd, args)`** — executes via `subprocess.Popen` with configurable shell
5. **`main()`** — entry point that prints YAML output and returns error count as exit code

**Special file conventions:**
- `.cmd` → input commands; `.out` → captured output; `.err` → output on error
- `.uone.cmd` → "update on error" variant: writes `.out` even if commands fail

**Entry point:** `kmdo = kmdo.cli:main` (console_scripts in `pyproject.toml`)

**Version:** single `__version__` string in `src/kmdo/__init__.py`

## CI/CD

GitHub Actions workflow (`.github/workflows/selftest.yml`):
- **build_and_check:** matrix of Ubuntu 22.04/24.04 + macOS × Python 3.10-3.13
- **test:** pytest on Ubuntu across Python 3.10-3.13
- **publish:** PyPI trusted publisher on version tags
