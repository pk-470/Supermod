"""Tests for the core helpers: env reading, local-mode detection, info printing."""

from __future__ import annotations

import re

import pytest

from supermod import _mode_setup, _utils

# --- get_and_verify_env ------------------------------------------------------


def test_get_and_verify_env_returns_value_when_set(monkeypatch):
    monkeypatch.setenv("SUPERMOD_TEST_VAR", "hello")
    assert _utils.get_and_verify_env("SUPERMOD_TEST_VAR") == "hello"


def test_get_and_verify_env_raises_when_unset(monkeypatch):
    monkeypatch.delenv("SUPERMOD_TEST_MISSING", raising=False)
    with pytest.raises(RuntimeError):
        _utils.get_and_verify_env("SUPERMOD_TEST_MISSING")


# --- is_local ----------------------------------------------------------------


def test_is_local_true_when_marker_exists(monkeypatch, tmp_path):
    marker = tmp_path / ".local"
    marker.write_text("")
    monkeypatch.setattr(_mode_setup, "LOCAL_MARKER", marker)
    _mode_setup.is_local.cache_clear()
    try:
        assert _mode_setup.is_local() is True
    finally:
        _mode_setup.is_local.cache_clear()


def test_is_local_false_when_marker_absent(monkeypatch, tmp_path):
    marker = tmp_path / "does_not_exist"
    monkeypatch.setattr(_mode_setup, "LOCAL_MARKER", marker)
    _mode_setup.is_local.cache_clear()
    try:
        assert _mode_setup.is_local() is False
    finally:
        _mode_setup.is_local.cache_clear()


# --- print_info --------------------------------------------------------------


def test_print_info_outputs_timezone_abbreviation(frozen_now, capsys):
    _utils.print_info("a message")
    out = capsys.readouterr().out
    assert "a message" in out
    # The timestamp should carry a real %Z abbreviation (EDT in summer / EST in
    # winter for America/Toronto), not a hardcoded literal.
    assert re.search(r"\b(EDT|EST)\b", out), out


def test_print_info_uses_dst_aware_abbreviation(frozen_now, capsys):
    """Mid-June abbreviation must be EDT (daylight), not EST."""
    _utils.print_info("summer")
    out = capsys.readouterr().out
    assert "EDT" in out, out
