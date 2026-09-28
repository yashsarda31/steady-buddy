from datetime import date, timedelta
import json

import pytest

from buddy.store import Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "buddy.db")


DAY = (date.today() - timedelta(days=1)).isoformat()


def test_food_portions_edit_and_restart(store):
    row_id = store.add_food(DAY, "Dal", 180, 1.5, "Lunch", True)
    assert store.food_total(DAY) == 270
    assert store.rows("favourites")[0]["calories"] == 180
    store.edit_food(row_id, "Dal", 200, 2, "Dinner")
    assert Store(store.path).food_total(DAY) == 400
    store.delete("foods", row_id)
    assert store.food_total(DAY) == 0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, "bad"])
def test_invalid_calories_never_write(store, value):
    with pytest.raises(ValueError):
        store.add_food(DAY, "Rice", value, 1, "Lunch")
    assert store.rows("foods") == []


@pytest.mark.parametrize("day", ["2026-02-30", "yesterday", "2099-01-01", "2026-9-1"])
def test_invalid_dates(store, day):
    with pytest.raises(ValueError):
        store.weigh(day, 75)


def test_daily_checkin_and_weighin_are_upserts(store):
    store.check_in(DAY, None, "Okay", "I showed up")
    assert store.habits(DAY)["alcohol_free"] == 0
    store.check_in(DAY, "free", "Good", "A short walk")
    store.check_in(DAY, "drank", "Low", "Honest check-in")
    assert len(store.rows("checkins")) == 1
    assert store.habits(DAY)["alcohol_free"] == 0
    store.weigh(DAY, 80)
    store.weigh(DAY, 79.8)
    assert len(store.rows("weights")) == 1
    assert store.rows("weights")[0]["kg"] == 79.8


def test_missing_dates_never_count_as_alcohol_free(store):
    store.check_in(DAY, "free", "Okay", "")
    store.add_workout(DAY, "Walk", 10)
    summary = store.habits(DAY)
    assert summary["alcohol_free"] == 1
    assert summary["checkins"] == 1
    assert summary["movement_days"] == 1
    assert summary["sessions"] == 1


def test_settings_and_round_trip(store, tmp_path):
    store.save_profile({"name": "Sam", "reason": "More energy", "timezone": "Asia/Kolkata",
                        "calorie_target": None, "weekly_sessions": 3})
    store.add_food(DAY, "Toast", 100, 2, "Breakfast", True)
    store.mark_complete(DAY, True)
    store.add_workout(DAY, "Walk", 10)
    store.weigh(DAY, 75)
    store.check_in(DAY, "free", "Good", "Logged food")
    other = Store(tmp_path / "other.db")
    other.restore(json.loads(store.export()))
    assert other.profile()["name"] == "Sam"
    assert other.food_total(DAY) == 200
    assert other.rows("diary_days")[0]["complete"] == 1
    assert other.habits(DAY)["alcohol_free"] == 1


def test_restore_is_atomic_on_bad_payload(store):
    store.add_food(DAY, "Keep me", 100, 1, "Snack")
    original = json.loads(store.export())
    bad = json.loads(store.export())
    bad["tables"]["weights"] = [{"day": DAY, "kg": -10}]
    with pytest.raises(ValueError):
        store.restore(bad)
    assert json.loads(store.export())["tables"] == original["tables"]
    bad["version"] = 99
    with pytest.raises(ValueError):
        store.restore(bad)
    assert store.food_total(DAY) == 100


def test_invalid_profile_does_not_change_saved_settings(store):
    original = store.profile()
    bad = {**original, "timezone": "Not/a/timezone"}
    with pytest.raises(ValueError):
        store.save_profile(bad)
    assert store.profile() == original


def test_table_identifiers_are_allowlisted(store):
    with pytest.raises(ValueError):
        store.rows("foods; DROP TABLE foods")
    with pytest.raises(ValueError):
        store.delete("settings", 1)


def test_empty_day_cannot_be_rewarded_as_complete(store):
    with pytest.raises(ValueError):
        store.mark_complete(DAY, True)


def test_editing_food_clears_completeness(store):
    row_id = store.add_food(DAY, "Meal", 100, 1, "Lunch")
    store.mark_complete(DAY, True)
    store.edit_food(row_id, "Meal", 200, 1, "Lunch")
    assert store.rows("diary_days", DAY) == []


def test_conflicting_backup_rolls_back_all_tables(store):
    store.add_food(DAY, "Keep me", 100, 1, "Lunch")
    bad = json.loads(store.export())
    bad["tables"]["favourites"] = [{"id": 1, "name": "Dal", "calories": 100},
                                       {"id": 2, "name": "DAL", "calories": 200}]
    with pytest.raises(ValueError):
        store.restore(bad)
    assert store.food_total(DAY) == 100
