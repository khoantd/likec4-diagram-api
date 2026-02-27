"""Basic tests around optional Turso integration wiring."""

from app.core.config import Settings
from app.services import db


def test_turso_disabled_by_default():
    settings = Settings()
    assert settings.turso_enabled is False


def test_init_turso_noop_when_disabled(monkeypatch):
    calls: list[object] = []

    def fake_connect(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("connect should not be called when Turso is disabled")

    monkeypatch.setattr(db, "turso", type("TursoModule", (), {"sync": type("Sync", (), {"connect": fake_connect})}))

    db.close_turso()
    db.init_turso()
    assert calls == []

