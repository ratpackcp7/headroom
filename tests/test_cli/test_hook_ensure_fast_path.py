from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from headroom.cli import _fast_init_hook_ensure
from headroom.install.models import DeploymentManifest
from headroom.install.state import load_manifest


def test_fast_init_hook_ensure_healthy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir = tmp_path / ".headroom" / "deploy" / "test-profile"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "manifest.json"
    manifest_file.write_text(
        json.dumps({
            "profile": "test-profile",
            "health_url": "http://127.0.0.1:8787/readyz",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["headroom", "init", "hook", "ensure", "--profile", "test-profile"])

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({"status": "healthy", "ready": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert _fast_init_hook_ensure() is True


def test_fast_init_hook_ensure_unreachable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir = tmp_path / ".headroom" / "deploy" / "test-profile"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "manifest.json"
    manifest_file.write_text(
        json.dumps({
            "profile": "test-profile",
            "health_url": "http://127.0.0.1:8787/readyz",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["headroom", "init", "hook", "ensure", "--profile", "test-profile"])

    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        assert _fast_init_hook_ensure() is False


def test_fast_init_hook_ensure_unhealthy_response(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir = tmp_path / ".headroom" / "deploy" / "test-profile"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "manifest.json"
    manifest_file.write_text(
        json.dumps({
            "profile": "test-profile",
            "health_url": "http://127.0.0.1:8787/readyz",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["headroom", "init", "hook", "ensure", "--profile", "test-profile"])

    mock_resp = MagicMock()
    mock_resp.status = 503
    mock_resp.read.return_value = json.dumps({"status": "unhealthy", "ready": False}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert _fast_init_hook_ensure() is False


def test_load_manifest_partial_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir = tmp_path / ".headroom" / "deploy" / "partial-profile"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "manifest.json"
    # Lacks preset, runtime_kind, supervisor_kind, scope, provider_mode, targets, backend
    manifest_file.write_text(
        json.dumps({
            "profile": "partial-profile",
            "health_url": "http://127.0.0.1:8787/readyz",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr("headroom.install.paths.deploy_root", lambda: tmp_path / ".headroom" / "deploy")
    m = load_manifest("partial-profile")
    assert isinstance(m, DeploymentManifest)
    assert m.profile == "partial-profile"
    assert m.health_url == "http://127.0.0.1:8787/readyz"
    assert m.port == 8787
    assert m.backend == "anthropic"
