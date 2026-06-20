"""Tests for the core helpers: env reading, local-mode detection, log formatting."""

from __future__ import annotations

import logging

import pendulum
import pytest

from supermod import _logging, _mode_setup, _utils

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


# --- TorontoFormatter --------------------------------------------------------


def _record_at(ts: float) -> logging.LogRecord:
    """Build an INFO record stamped at a chosen POSIX timestamp."""
    record = logging.LogRecord(
        name="supermod.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="a message",
        args=None,
        exc_info=None,
    )
    record.created = ts
    return record


def test_formatter_summer_uses_edt():
    """A summer timestamp renders the DST abbreviation (EDT), not a literal."""
    ts = pendulum.datetime(2026, 6, 17, 12, 0, 0, tz="America/Toronto").timestamp()
    out = _logging.TorontoFormatter("%(asctime)s [%(levelname)s] %(message)s").format(
        _record_at(ts)
    )
    assert "a message" in out
    assert "EDT" in out, out


def test_formatter_winter_uses_est():
    """A winter timestamp renders the standard abbreviation (EST)."""
    ts = pendulum.datetime(2026, 1, 17, 12, 0, 0, tz="America/Toronto").timestamp()
    out = _logging.TorontoFormatter("%(asctime)s [%(levelname)s] %(message)s").format(
        _record_at(ts)
    )
    assert "EST" in out, out
