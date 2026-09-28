import json

import pytest

from buddy.hosting import cloud_hosting, cloud_store
from buddy.store import local_today


def test_cloud_detection_uses_actual_hostname(monkeypatch):
    monkeypatch.delenv("BUDDY_HOSTING", raising=False)
    assert cloud_hosting("https://steady-buddy.streamlit.app/~/+/food")
    assert not cloud_hosting("https://streamlit.app.example.com/")
    assert not cloud_hosting("http://localhost:8501/")


def test_browser_diaries_are_isolated(tmp_path):
    first = cloud_store(tmp_path, {"token": "a" * 64})
    second = cloud_store(tmp_path, {"token": "b" * 64})
    first.add_food(local_today().isoformat(), "Dal", 180, 1.5, "Lunch")
    assert not second.rows("foods")
    assert cloud_store(tmp_path, {"token": "a" * 64}).rows("foods")[0]["name"] == "Dal"


def test_browser_backup_restores_after_server_files_reset(tmp_path):
    original = cloud_store(tmp_path / "old", {"token": "a" * 64})
    original.add_food(local_today().isoformat(), "Dal", 180, 1.5, "Lunch")
    profile = original.profile()
    profile["name"] = "Sam"
    original.save_profile(profile)
    backup = original.export()
    recovered = cloud_store(tmp_path / "new", {"token": "a" * 64, "backup": backup})
    assert json.loads(recovered.export()) == json.loads(backup)
    # An older browser tab must never overwrite the newer server diary.
    recovered.add_food(local_today().isoformat(), "Rice", 200, 1, "Lunch")
    assert len(cloud_store(tmp_path / "new", {"token": "a" * 64, "backup": backup}).rows("foods")) == 2


@pytest.mark.parametrize("identity", [None, {}, {"token": "../diary"}, {"token": "a" * 63}])
def test_invalid_browser_identity_cannot_select_a_diary(tmp_path, identity):
    with pytest.raises(ValueError, match="identified"):
        cloud_store(tmp_path, identity)
    assert not list(tmp_path.iterdir())


def test_invalid_backup_stays_retryable(tmp_path):
    with pytest.raises(ValueError, match="restored"):
        cloud_store(tmp_path, {"token": "a" * 64, "backup": "not json"})
    assert not list((tmp_path / "devices").glob("*.db"))
    assert not cloud_store(tmp_path, {"token": "a" * 64}).rows("foods")
