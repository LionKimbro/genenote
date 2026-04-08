import os
import sys
from pathlib import Path

from genenote import windows


def test_intercept_genenote_launcher_invocation_changes_cwd_and_strips_argv(tmp_path, monkeypatch):
    launcher = tmp_path / "base.genenote"
    launcher.write_text("", encoding="utf-8")

    monkeypatch.chdir(Path.cwd())
    monkeypatch.setattr(sys, "argv", ["genenote", str(launcher)])

    changed = windows.intercept_genenote_launcher_invocation()

    assert changed is True
    assert Path.cwd() == tmp_path
    assert sys.argv == ["genenote"]


def test_rewrite_base_command_argv_converts_extra_positional_target(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["genenote", "base", str(tmp_path)])

    changed = windows.rewrite_base_command_argv()

    assert changed is True
    assert sys.argv[1] == "--path.target_folder"
    assert sys.argv[2] == str(tmp_path.resolve())
    assert sys.argv[3] == "base"


def test_command_base_creates_launcher_and_project_structure(tmp_path):
    launcher_path = windows.command_base(tmp_path)

    assert launcher_path == tmp_path / "base.genenote"
    assert launcher_path.exists()
    assert (tmp_path / ".genenote" / "project.json").exists()
    assert (tmp_path / ".genenote" / "nodes").exists()


def test_build_open_command_uses_placeholder():
    command = windows.build_open_command("%1")
    assert '"%1"' in command


def test_build_base_command_uses_base_and_placeholder():
    command = windows.build_base_command("%1")
    assert ' base ' in command
    assert '"%1"' in command
