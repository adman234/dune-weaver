"""Tests for crash-safe JSON writes and corrupt-file preservation."""
import json
import os

import pytest

from modules.core import atomic_io


def test_atomic_write_json_roundtrip(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text('{"old": true}')
    atomic_io.atomic_write_json(target, {"new": 1}, indent=2)
    assert json.loads(target.read_text()) == {"new": 1}
    # No temp files left behind
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_failed_write_keeps_original(tmp_path):
    target = tmp_path / "playlists.json"
    target.write_text('{"keep": 1}')
    with pytest.raises(TypeError):
        atomic_io.atomic_write_json(target, {"bad": object()})
    assert json.loads(target.read_text()) == {"keep": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["playlists.json"]


def test_preserve_corrupt_file(tmp_path):
    target = tmp_path / "playlists.json"
    target.write_text("{not json")
    copy = atomic_io.preserve_corrupt_file(target)
    assert copy and os.path.basename(copy).startswith("playlists.json.corrupt-")
    with open(copy) as f:
        assert f.read() == "{not json"
    assert atomic_io.preserve_corrupt_file(tmp_path / "missing.json") is None


def test_corrupt_playlists_are_preserved(tmp_path, monkeypatch):
    from modules.core import playlist_manager
    target = tmp_path / "playlists.json"
    target.write_text("{truncated")
    monkeypatch.setattr(playlist_manager, "PLAYLISTS_FILE", str(target))
    assert playlist_manager.load_playlists() == {}
    assert json.loads(target.read_text()) == {}
    assert any(p.name.startswith("playlists.json.corrupt-") for p in tmp_path.iterdir())
