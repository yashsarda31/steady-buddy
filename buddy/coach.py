"""Deterministic, non-judgmental support; no chatbot or medical prescription."""
from datetime import date, timedelta

MESSAGES = {
    "Impatient": {
        "title": "Give your effort time to work.",
        "body": "A single weigh-in is a moment, not the whole story. You don't need to rush, skip meals, "
                "or make tomorrow harder. Look at the habits you can repeat this week.",
        "action": "Choose one small action for today. Check your weight trend next week."},
    "No motivation": {
        "title": "Make the first step smaller.",
        "body": "You don't have to feel motivated to begin. A few comfortable minutes of movement "
                "can be today's whole plan. Rest is a valid choice when you need it.",
        "action": "Put on your shoes and try a gentle five-minute walk, if it feels comfortable."},
    "Want a drink": {
        "title": "You only have to choose the next moment.",
        "body": "A craving is a feeling you can notice without acting on it. Pause, name what you're "
                "feeling, and put an alcohol-free drink within reach. Ask someone you trust for support.",
        "action": "Take a two-minute pause, change rooms, then choose what helps you feel steady."},
    "A difficult day": {
        "title": "You can return with the next choice.",
        "body": "One meal, a missed workout, or a drink doesn't erase the work you've done. "
                "Keep your next meal normal. There is nothing to punish yourself for.",
        "action": "Write one kind sentence to yourself and pick a manageable next step."},
    "Doing well": {
        "title": "Notice what is becoming easier.",
        "body": "The ordinary days count. Logging honestly, making time to move, and choosing "
                "an alcohol-free evening are all things you can be proud of.",
        "action": "Save a small win so future you can see the progress beyond the scale."},
}


def message(situation, reason):
    result = dict(MESSAGES.get(situation, MESSAGES["A difficult day"]))
    result["reason"] = f"Your reason: {reason}"
    return result


def weight_trend(rows):
    rows = sorted(rows, key=lambda row: row["day"])
    points = []
    for row in rows:
        start = (date.fromisoformat(row["day"]) - timedelta(days=6)).isoformat()
        window = [other["kg"] for other in rows if start <= other["day"] <= row["day"]]
        points.append({"Date": row["day"], "Weight": row["kg"],
                       "7-day average": round(sum(window) / len(window), 2),
                       "Measurements in window": len(window)})
    return points
