from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

from buddy.store import Store

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDDY_DB_PATH", str(tmp_path / "buddy.db"))
    # AppTest makes a fresh runtime for each instance; CCv2 registration belongs to that runtime.
    sys.modules.pop("buddy.timer", None)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()


@pytest.mark.parametrize("page", ["today", "food", "move", "buddy", "progress", "settings"])
def test_pages_render_without_exceptions(app, page):
    app.switch_page(f"app_pages/{page}.py").run()
    assert not app.exception


def test_food_submission_and_restart(app):
    app.switch_page("app_pages/food.py").run()
    app.text_input(key="food_name").set_value("Dal")
    app.number_input(key="food_calories").set_value(180.0)
    app.number_input(key="food_portions").set_value(1.5)
    app.button[0].click().run()
    assert not app.exception
    store = app.session_state["store"]
    assert store.food_total(app.session_state["today"].isoformat()) == 270
    assert Store(store.path).rows("foods")[0]["name"] == "Dal"


def test_blank_food_has_friendly_error(app):
    app.switch_page("app_pages/food.py").run()
    app.button[0].click().run()
    assert app.error and not app.exception
    assert app.session_state["store"].rows("foods") == []


def test_workout_and_weight(app):
    app.switch_page("app_pages/move.py").run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["store"].rows("workouts")[0]["minutes"] == 10
    app.switch_page("app_pages/progress.py").run()
    app.number_input(key="weight_kg").set_value(78.2)
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["store"].rows("weights")[0]["kg"] == 78.2


def test_checkin_and_craving_ui(app):
    today = app.session_state["today"].isoformat()
    app.selectbox(key=f"today_alcohol_{today}").select("Alcohol-free")
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["store"].habits(today)["alcohol_free"] == 1
    app.switch_page("app_pages/buddy.py").run()
    app.selectbox(key="buddy_situation").select("Want a drink").run()
    assert not app.exception
    assert app.warning


def test_optional_calorie_reference_and_name(app):
    app.switch_page("app_pages/settings.py").run()
    app.text_input(key="profile_name").set_value("Sam")
    app.checkbox(key="profile_use_target").check()
    app.number_input(key="profile_target").set_value(2200.0)
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["store"].profile()["calorie_target"] == 2200
    app.switch_page("app_pages/today.py").run()
    assert any("Sam" in row.value for row in app.header)
