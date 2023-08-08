#!/usr/bin/env python3
"""
    Run commands from .cmd files, storing output in .out files
"""
from __future__ import print_function

import argparse
import os
import sys
from subprocess import PIPE, Popen


def expand_path(path):
    """Expand variables in and provide absolute version of the given 'path'"""

    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def update_file(fpath, content):
    """Writes 'content' to 'fpath'"""

    with open(fpath, "w+") as output:
        output.write(content)


def cmd_run(cmd, args):
    """Execute the given command and return stdout, stderr, and returncode"""

    with Popen(
        cmd, shell=True, stdout=PIPE, stderr=PIPE, executable=args.shell
    ) as process:
        out, err = process.communicate()

    return out, err, process.returncode


def cmd_from_file(fpath):
    """Produces a 'cmd' as a list of strings from the given 'fpath'"""

    # Grab commands
    with open(fpath) as cmdfd:
        cmds = [line.strip() for line in cmdfd.readlines()]

    # Merge those line-continuations
    cmds = "\n".join(cmds).replace("\\\n", "").splitlines()

    if not cmds:
        fname = os.path.basename(fpath)
        cmds = [fname.replace(".uone", "").replace(".cmd", "")]

    return cmds


def produce_cmd_output(args):
    """Do the actual work"""

    for root, _, fnames in os.walk(args.path):
        if args.recursive and root != args.path:
            continue

        for fname in sorted(fname for fname in fnames if fname.endswith(".cmd")):
            if args.exclude and args.exclude in fname:
                continue

            cmd_fpath = os.sep.join([root, fname])

            out_fpath = cmd_fpath.replace(".cmd", ".out")
            err_fpath = cmd_fpath.replace(".cmd", ".err")
            uone = cmd_fpath.endswith(".uone.cmd")
            output = []
            errored = False

            for cmd in cmd_from_file(cmd_fpath):
                stdout, stderr, rcode = cmd_run(cmd, args)

                output.append(stdout)
                output.append(stderr)

                err = bool(rcode) and not uone
                errored |= err

                yield out_fpath, cmd_fpath, cmd, rcode, uone, err

            if errored:
                update_file(err_fpath, "\n".join([o.decode("utf-8") for o in output]))

            if not errored or uone:
                update_file(out_fpath, "\n".join([o.decode("utf-8") for o in output]))


def parse_args():
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


def main():
    """Entry point"""

    args = parse_args()

    nerrs = 0

    try:
        print("args:")
        print("  path: %r" % args.path)
        print("  recursive: %r" % args.recursive)
        print("results:")
        for out_fp, cmd_fp, cmd, rcode, uone, err in produce_cmd_output(args):
            nerrs += int(err)

            print("- out_fp: %r" % out_fp)
            print("  cmd_fp: %r" % cmd_fp)
            print("  cmd: %r" % cmd)
            print("  rcode: %r" % rcode)
            print("  uone: %r" % uone)
            print("  err: %r" % err)

    except OSError as exc:
        print("# err(%s)" % exc)
        return 1

    print("nerrs: %r" % nerrs)

    return nerrs
