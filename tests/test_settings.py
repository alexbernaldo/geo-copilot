"""Tests para geo/settings.py."""

import os
import stat
from pathlib import Path

import pytest

from geo import settings


@pytest.fixture
def env_path(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    monkeypatch.setattr(settings, "ENV_PATH", p)
    # reset env relevantes
    for k in settings.DEFAULTS:
        monkeypatch.delenv(k, raising=False)
    return p


def test_save_creates_600_and_updates_env(env_path):
    settings.save({"LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "sk-or-test-123"})
    assert env_path.exists()
    mode = env_path.stat().st_mode & 0o777
    assert mode == 0o600
    assert os.environ["LLM_PROVIDER"] == "openrouter"
    assert os.environ["OPENROUTER_API_KEY"] == "sk-or-test-123"


def test_save_preserves_comments_and_unknown(env_path):
    env_path.write_text("# comentario\nFOO=bar\nLLM_PROVIDER=mock\n", encoding="utf-8")
    settings.save({"LLM_PROVIDER": "openrouter"})
    text = env_path.read_text(encoding="utf-8")
    assert "# comentario" in text
    assert "FOO=bar" in text


def test_save_replaces_without_duplicate(env_path):
    env_path.write_text("LLM_PROVIDER=mock\n", encoding="utf-8")
    settings.save({"LLM_PROVIDER": "openrouter"})
    lines = [l for l in env_path.read_text().splitlines() if l.startswith("LLM_PROVIDER=")]
    assert len(lines) == 1
    assert lines[0] == "LLM_PROVIDER=openrouter"


def test_get_strips_inline_comment(env_path, monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "google/gemini-2.5-flash  # comentario")
    assert settings.get("LLM_MODEL") == "google/gemini-2.5-flash"


def test_get_does_not_strip_secret(env_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-abc # not a comment")
    assert settings.get("OPENROUTER_API_KEY") == "sk-or-abc # not a comment"


def test_mask_max_visible(env_path):
    key = "sk-or-v1-abcdefghwxyz"
    m = settings.mask(key)
    # visible chars <= 11
    visible = m.replace("…", "")
    assert len(visible) <= 11