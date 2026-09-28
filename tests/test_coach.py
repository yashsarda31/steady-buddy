from datetime import date, timedelta

from buddy.coach import message, weight_trend


def test_every_situation_has_supportive_action():
    for situation in ["Impatient", "No motivation", "Want a drink", "A difficult day", "Doing well"]:
        result = message(situation, "More energy")
        assert result["title"] and result["body"] and result["action"]
        assert "More energy" in result["reason"]
        assert "burn off" not in result["body"].lower()


def test_trend_uses_calendar_window_not_last_seven_measurements():
    today = date.today()
    old = (today - timedelta(days=30)).isoformat()
    recent = (today - timedelta(days=2)).isoformat()
    rows = [{"day": old, "kg": 90}, {"day": recent, "kg": 80}, {"day": today.isoformat(), "kg": 82}]
    points = weight_trend(rows)
    assert points[-1]["7-day average"] == 81
    assert points[-1]["Measurements in window"] == 2


def test_empty_trend():
    assert weight_trend([]) == []
