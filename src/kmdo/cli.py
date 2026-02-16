#!/usr/bin/env python3
"""
    Run commands from .cmd files, storing output in .out files
"""
import argparse
import json
import signal
import subprocess
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Generator

_interrupted = False


def _handle_signal(signum, frame):
    global _interrupted
    _interrupted = True


def expand_path(path: str) -> Path:
    """Expand variables in and provide absolute version of the given 'path'"""

    return Path(path).expanduser().resolve()


def update_file(fpath: Path, content: str) -> None:
    """Writes 'content' to 'fpath'"""

    fpath.write_text(content)


def cmd_run(
    cmd: str, args: argparse.Namespace
) -> tuple[bytes, bytes, int]:
    """Execute the given command and return stdout, stderr, and returncode"""

    with Popen(
        cmd, shell=True, stdout=PIPE, stderr=PIPE, executable=args.shell
    ) as process:
        try:
            out, err = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
            return out, err, -1

    return out, err, process.returncode


def cmd_from_file(fpath: Path) -> list[str]:
    """Produces a 'cmd' as a list of strings from the given 'fpath'"""

    cmds = [line.strip() for line in fpath.read_text().splitlines()]

    # Merge those line-continuations
    cmds = "\n".join(cmds).replace("\\\n", "").splitlines()

    if not cmds:
        cmds = [fpath.name.replace(".uone", "").replace(".cmd", "")]

    return cmds


def produce_cmd_output(
    args: argparse.Namespace,
) -> Generator[tuple[Path, Path, str, int | None, bool, bool], None, None]:
    """Do the actual work"""

    for item in sorted(args.path.rglob("*.cmd")):
        if _interrupted:
            break
        if not item.is_file():
            continue
        if args.recursive and item.parent != args.path:
            continue
        if args.exclude and args.exclude in item.name:
            continue

        cmd_fpath = item
        out_fpath = cmd_fpath.parent / cmd_fpath.name.replace(".cmd", ".out")
        err_fpath = cmd_fpath.parent / cmd_fpath.name.replace(".cmd", ".err")
        uone = cmd_fpath.name.endswith(".uone.cmd")
        output: list[bytes] = []
        errored = False

        for cmd in cmd_from_file(cmd_fpath):
            if _interrupted:
                break

            if args.dry_run:
                yield out_fpath, cmd_fpath, cmd, None, uone, False
                continue

            stdout, stderr, rcode = cmd_run(cmd, args)

            output.append(stdout)
            output.append(stderr)

            err = bool(rcode) and not uone
            errored |= err

            yield out_fpath, cmd_fpath, cmd, rcode, uone, err

        if args.dry_run:
            continue

        if errored:
            update_file(err_fpath, "\n".join(o.decode("utf-8") for o in output))

        if not errored or uone:
            update_file(out_fpath, "\n".join(o.decode("utf-8") for o in output))


def _yaml_val(val) -> str:
    """Format a Python value as a YAML scalar."""

    if val is None:
        return "null"
    if isinstance(val, bool):
        return str(val).lower()
    if isinstance(val, str):
        return repr(val)
    return str(val)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run commands from .cmd files, storing output in .out files"
    )
    parser.add_argument("path", type=str, help="Path to DIR containing .cmd files")
    parser.add_argument("-r", "--recursive", action="store_true", help="go deepah!")
    parser.add_argument("-s", "--shell", help="Absolute path to the Shell to use")
    parser.add_argument("-x", "--exclude", help="Exclude command-files matching this")
    parser.add_argument(
        "-f",
        "--output-format",
        choices=["yaml", "jsonl"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="List commands without executing them",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds for each command",
    )

    args = parser.parse_args()
    args.path = expand_path(args.path)

    return args


def main() -> int:
    """Entry point"""

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    args = parse_args()

    nerrs = 0
    fmt = args.output_format

    try:
        if fmt == "jsonl":
            # JSON Lines: one JSON object per result, streamed
            for out_fp, cmd_fp, cmd, rcode, uone, err in produce_cmd_output(args):
                nerrs += int(err)
                print(json.dumps({
                    "out_fp": str(out_fp),
                    "cmd_fp": str(cmd_fp),
                    "cmd": cmd,
                    "rcode": rcode,
                    "uone": uone,
                    "err": err,
                }))

        else:
            # YAML (default): stream results as they arrive
            print("args:")
            print(f"  path: {str(args.path)!r}")
            print(f"  recursive: {str(args.recursive).lower()}")
            print("results:")
            for out_fp, cmd_fp, cmd, rcode, uone, err in produce_cmd_output(args):
                nerrs += int(err)
                print(f"- out_fp: {str(out_fp)!r}")
                print(f"  cmd_fp: {str(cmd_fp)!r}")
                print(f"  cmd: {cmd!r}")
                print(f"  rcode: {_yaml_val(rcode)}")
                print(f"  uone: {str(uone).lower()}")
                print(f"  err: {str(err).lower()}")
            print(f"nerrs: {nerrs}")

    except OSError as exc:
        print(f"# err({exc})")
        return 1

    return nerrs
