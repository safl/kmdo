#!/usr/bin/env python3
"""
    Run commands from .cmd files, storing output in .out files
"""
import argparse
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Generator


def expand_path(path: str) -> Path:
    """Expand variables in and provide absolute version of the given 'path'"""

    return Path(path).expanduser().resolve()


def update_file(fpath: Path, content: str) -> None:
    """Writes 'content' to 'fpath'"""

    fpath.write_text(content)


def cmd_run(cmd: str, args: argparse.Namespace) -> tuple[bytes, bytes, int]:
    """Execute the given command and return stdout, stderr, and returncode"""

    with Popen(
        cmd, shell=True, stdout=PIPE, stderr=PIPE, executable=args.shell
    ) as process:
        out, err = process.communicate()

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
) -> Generator[tuple[Path, Path, str, int, bool, bool], None, None]:
    """Do the actual work"""

    for item in sorted(args.path.rglob("*.cmd")):
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
            stdout, stderr, rcode = cmd_run(cmd, args)

            output.append(stdout)
            output.append(stderr)

            err = bool(rcode) and not uone
            errored |= err

            yield out_fpath, cmd_fpath, cmd, rcode, uone, err

        if errored:
            update_file(err_fpath, "\n".join(o.decode("utf-8") for o in output))

        if not errored or uone:
            update_file(out_fpath, "\n".join(o.decode("utf-8") for o in output))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run commands from .cmd files, storing output in .out files"
    )
    parser.add_argument("path", type=str, help="Path to DIR containing .cmd files")
    parser.add_argument("-r", "--recursive", action="store_true", help="go deepah!")
    parser.add_argument("-s", "--shell", help="Absolute path to the Shell to use")
    parser.add_argument("-x", "--exclude", help="Exclude command-files matching this")

    args = parser.parse_args()
    args.path = expand_path(args.path)

    return args


def main() -> int:
    """Entry point"""

    args = parse_args()

    nerrs = 0

    try:
        print("args:")
        print(f"  path: {str(args.path)!r}")
        print(f"  recursive: {str(args.recursive).lower()}")
        print("results:")
        for out_fp, cmd_fp, cmd, rcode, uone, err in produce_cmd_output(args):
            nerrs += int(err)

            print(f"- out_fp: {str(out_fp)!r}")
            print(f"  cmd_fp: {str(cmd_fp)!r}")
            print(f"  cmd: {cmd!r}")
            print(f"  rcode: {rcode}")
            print(f"  uone: {str(uone).lower()}")
            print(f"  err: {str(err).lower()}")

    except OSError as exc:
        print(f"# err({exc})")
        return 1

    print(f"nerrs: {nerrs}")

    return nerrs
