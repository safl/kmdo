"""Tests for kmdo.cli"""
import argparse
from pathlib import Path

from kmdo.cli import cmd_from_file, cmd_run, expand_path, produce_cmd_output, update_file


def make_args(path: Path, recursive: bool = False, shell: str | None = None, exclude: str | None = None) -> argparse.Namespace:
    """Helper to build an args namespace."""
    return argparse.Namespace(path=path, recursive=recursive, shell=shell, exclude=exclude)


class TestExpandPath:
    def test_resolves_relative(self, tmp_path):
        result = expand_path(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_expands_home(self):
        result = expand_path("~")
        assert result == Path.home()


class TestUpdateFile:
    def test_writes_content(self, tmp_path):
        fpath = tmp_path / "test.out"
        update_file(fpath, "hello world")
        assert fpath.read_text() == "hello world"

    def test_overwrites_existing(self, tmp_path):
        fpath = tmp_path / "test.out"
        fpath.write_text("old")
        update_file(fpath, "new")
        assert fpath.read_text() == "new"


class TestCmdRun:
    def test_captures_stdout(self):
        args = make_args(Path("."))
        out, err, rcode = cmd_run("echo hello", args)
        assert out.strip() == b"hello"
        assert rcode == 0

    def test_captures_stderr(self):
        args = make_args(Path("."))
        _, stderr, _ = cmd_run("echo error >&2", args)
        assert stderr.strip() == b"error"

    def test_returns_nonzero_on_failure(self):
        args = make_args(Path("."))
        _, _, rcode = cmd_run("false", args)
        assert rcode != 0


class TestCmdFromFile:
    def test_reads_commands(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello\necho world\n")
        cmds = cmd_from_file(cmd_file)
        assert cmds == ["echo hello", "echo world"]

    def test_merges_line_continuations(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo \\\nhello\n")
        cmds = cmd_from_file(cmd_file)
        assert cmds == ["echo hello"]

    def test_empty_file_uses_filename(self, tmp_path):
        cmd_file = tmp_path / "mycommand.cmd"
        cmd_file.write_text("")
        cmds = cmd_from_file(cmd_file)
        assert cmds == ["mycommand"]

    def test_empty_uone_file_strips_extensions(self, tmp_path):
        cmd_file = tmp_path / "mycommand.uone.cmd"
        cmd_file.write_text("")
        cmds = cmd_from_file(cmd_file)
        assert cmds == ["mycommand"]


class TestProduceCmdOutput:
    def test_basic_execution(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")
        args = make_args(tmp_path)

        results = list(produce_cmd_output(args))
        assert len(results) == 1

        out_fp, cmd_fp, cmd, rcode, uone, err = results[0]
        assert out_fp == tmp_path / "test.out"
        assert cmd_fp == cmd_file
        assert cmd == "echo hello"
        assert rcode == 0
        assert uone is False
        assert err is False

    def test_creates_out_file(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")
        args = make_args(tmp_path)

        list(produce_cmd_output(args))

        out_file = tmp_path / "test.out"
        assert out_file.exists()
        assert "hello" in out_file.read_text()

    def test_error_creates_err_file(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("false")
        args = make_args(tmp_path)

        results = list(produce_cmd_output(args))
        assert results[0][5] is True  # err=True

        err_file = tmp_path / "test.err"
        assert err_file.exists()

    def test_uone_creates_out_on_error(self, tmp_path):
        cmd_file = tmp_path / "test.uone.cmd"
        cmd_file.write_text("echo output && false")
        args = make_args(tmp_path)

        results = list(produce_cmd_output(args))
        assert results[0][4] is True   # uone=True
        assert results[0][5] is False  # err=False (uone suppresses)

        out_file = tmp_path / "test.uone.out"
        assert out_file.exists()

    def test_exclude_skips_matching(self, tmp_path):
        (tmp_path / "include.cmd").write_text("echo yes")
        (tmp_path / "exclude_me.cmd").write_text("echo no")
        args = make_args(tmp_path, exclude="exclude")

        results = list(produce_cmd_output(args))
        assert len(results) == 1
        assert results[0][2] == "echo yes"

    def test_recursive_flag_limits_depth(self, tmp_path):
        (tmp_path / "top.cmd").write_text("echo top")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "deep.cmd").write_text("echo deep")

        # With -r, only top-level
        args = make_args(tmp_path, recursive=True)
        results = list(produce_cmd_output(args))
        assert len(results) == 1
        assert results[0][2] == "echo top"

    def test_without_recursive_walks_subdirs(self, tmp_path):
        (tmp_path / "top.cmd").write_text("echo top")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "deep.cmd").write_text("echo deep")

        args = make_args(tmp_path, recursive=False)
        results = list(produce_cmd_output(args))
        assert len(results) == 2

    def test_multiple_commands_in_file(self, tmp_path):
        cmd_file = tmp_path / "multi.cmd"
        cmd_file.write_text("echo one\necho two\n")
        args = make_args(tmp_path)

        results = list(produce_cmd_output(args))
        assert len(results) == 2
        assert results[0][2] == "echo one"
        assert results[1][2] == "echo two"
