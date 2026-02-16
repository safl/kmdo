"""Tests for kmdo.cli"""
import argparse
import json
from pathlib import Path

from kmdo.cli import (
    _yaml_val,
    cmd_from_file,
    cmd_run,
    expand_path,
    produce_cmd_output,
    update_file,
)


def make_args(
    path: Path,
    recursive: bool = False,
    shell: str | None = None,
    exclude: str | None = None,
    dry_run: bool = False,
    timeout: float | None = None,
    output_format: str = "yaml",
) -> argparse.Namespace:
    """Helper to build an args namespace."""
    return argparse.Namespace(
        path=path,
        recursive=recursive,
        shell=shell,
        exclude=exclude,
        dry_run=dry_run,
        timeout=timeout,
        output_format=output_format,
    )


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

    def test_timeout_kills_slow_command(self):
        args = make_args(Path("."), timeout=0.1)
        _, _, rcode = cmd_run("sleep 10", args)
        assert rcode == -1


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


class TestDryRun:
    def test_does_not_execute(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")
        args = make_args(tmp_path, dry_run=True)

        results = list(produce_cmd_output(args))
        assert len(results) == 1
        _, _, cmd, rcode, _, err = results[0]
        assert cmd == "echo hello"
        assert rcode is None
        assert err is False

    def test_does_not_create_files(self, tmp_path):
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")
        args = make_args(tmp_path, dry_run=True)

        list(produce_cmd_output(args))
        assert not (tmp_path / "test.out").exists()
        assert not (tmp_path / "test.err").exists()


class TestTimeout:
    def test_timeout_in_produce_cmd_output(self, tmp_path):
        cmd_file = tmp_path / "slow.cmd"
        cmd_file.write_text("sleep 10")
        args = make_args(tmp_path, timeout=0.1)

        results = list(produce_cmd_output(args))
        assert len(results) == 1
        assert results[0][3] == -1  # rcode
        assert results[0][5] is True  # err


class TestYamlVal:
    def test_none(self):
        assert _yaml_val(None) == "null"

    def test_bool_true(self):
        assert _yaml_val(True) == "true"

    def test_bool_false(self):
        assert _yaml_val(False) == "false"

    def test_string(self):
        assert _yaml_val("hello") == "'hello'"

    def test_int(self):
        assert _yaml_val(42) == "42"


class TestMainOutput:
    def test_yaml_output_is_streamed(self, tmp_path, capsys):
        import sys
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")

        sys.argv = ["kmdo", str(tmp_path)]
        from kmdo.cli import main
        rcode = main()
        assert rcode == 0

        captured = capsys.readouterr()
        assert captured.out.startswith("args:\n")
        assert "results:" in captured.out
        assert "nerrs: 0" in captured.out

    def test_jsonl_output(self, tmp_path, capsys):
        import sys
        cmd_file = tmp_path / "test.cmd"
        cmd_file.write_text("echo hello")

        sys.argv = ["kmdo", "-f", "jsonl", str(tmp_path)]
        from kmdo.cli import main
        rcode = main()
        assert rcode == 0

        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["cmd"] == "echo hello"
        assert parsed["rcode"] == 0

