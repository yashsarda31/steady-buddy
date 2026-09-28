"""Small, validated SQLite diary. Connections never outlive an operation."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import csv
import io
import json
import math
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MEALS = ("Breakfast", "Lunch", "Dinner", "Snack", "Drink")
MOODS = ("Good", "Okay", "Low", "Stressed")
TABLES = ("foods", "workouts", "weights", "checkins", "favourites", "diary_days")
DEFAULT_PROFILE = {"name": "Friend", "reason": "Feel healthier and have more energy",
                   "timezone": "Asia/Kolkata", "calorie_target": None, "weekly_sessions": 3}


def text(value, label, limit=200, required=True):
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise ValueError(f"{label}: enter {'1–' if required else 'up to '}{limit} characters.")
    return value.strip()


def number(value, label, low, high):
    if isinstance(value, bool):
        raise ValueError(f"{label}: enter a number.")
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{label}: enter a number.") from None
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f"{label}: enter a value between {low} and {high}.")
    return result


def local_today(timezone="Asia/Kolkata"):
    return datetime.now(ZoneInfo(timezone)).date()


def valid_day(value, timezone="Asia/Kolkata"):
    try:
        result = date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("Choose a valid calendar date.") from None
    if result.isoformat() != value or result > local_today(timezone):
        raise ValueError("Choose today or an earlier date in YYYY-MM-DD format.")
    return value


def valid_profile(profile):
    if not isinstance(profile, dict) or set(profile) != set(DEFAULT_PROFILE):
        raise ValueError("This profile has missing or unsupported settings.")
    result = dict(profile)
    result["name"] = text(profile["name"], "Name", 60)
    result["reason"] = text(profile["reason"], "Your reason", 400)
    try:
        ZoneInfo(profile["timezone"])
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValueError("Choose a recognised timezone.") from None
    if profile["calorie_target"] is not None:
        result["calorie_target"] = number(profile["calorie_target"], "Calorie reference", 100, 10000)
    sessions = number(profile["weekly_sessions"], "Weekly sessions", 1, 14)
    if sessions != int(sessions):
        raise ValueError("Weekly sessions must be a whole number.")
    result["weekly_sessions"] = int(sessions)
    return result


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("This diary belongs to a newer app version. Keep it and update the app.")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS foods (
                    id INTEGER PRIMARY KEY, day TEXT NOT NULL, name TEXT NOT NULL,
                    calories REAL NOT NULL, portions REAL NOT NULL, meal TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS food_day ON foods(day);
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY, day TEXT NOT NULL, name TEXT NOT NULL, minutes INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS weights (day TEXT PRIMARY KEY, kg REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS checkins (
                    day TEXT PRIMARY KEY, alcohol TEXT, mood TEXT NOT NULL, win TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS favourites (
                    id INTEGER PRIMARY KEY, name TEXT UNIQUE COLLATE NOCASE NOT NULL, calories REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS diary_days (day TEXT PRIMARY KEY, complete INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK (id=1), profile TEXT NOT NULL);
                PRAGMA user_version=1;
            """)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def profile(self):
        with self.connection() as conn:
            row = conn.execute("SELECT profile FROM settings WHERE id=1").fetchone()
        return valid_profile(json.loads(row[0])) if row else dict(DEFAULT_PROFILE)

    def save_profile(self, profile):
        profile = valid_profile(profile)
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings VALUES (1, ?)", (json.dumps(profile),))

    def day(self, day):
        return valid_day(day, self.profile()["timezone"])

    def rows(self, table, day=None):
        if table not in TABLES:
            raise ValueError("Unsupported diary table.")
        order = "name" if table == "favourites" else "day DESC"
        if table in ("foods", "workouts"):
            order += ", id DESC"
        if day is not None and table == "favourites":
            raise ValueError("Favourites do not have a date.")
        with self.connection() as conn:
            if day is None:
                rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
            else:
                rows = conn.execute(f"SELECT * FROM {table} WHERE day=? ORDER BY {order}", (self.day(day),)).fetchall()
        return [dict(row) for row in rows]

    def food_values(self, name, calories, portions, meal):
        if meal not in MEALS:
            raise ValueError("Choose a recognised meal.")
        return (text(name, "Food name"), number(calories, "Calories per serving", 0, 10000),
                number(portions, "Servings", 0.1, 50), meal)

    def add_food(self, day, name, calories, portions, meal, save_favourite=False):
        day = self.day(day)
        values = self.food_values(name, calories, portions, meal)
        with self.connection() as conn:
            row_id = conn.execute("INSERT INTO foods(day,name,calories,portions,meal) VALUES (?,?,?,?,?)",
                                  (day, *values)).lastrowid
            if save_favourite:
                conn.execute("INSERT INTO favourites(name,calories) VALUES (?,?) ON CONFLICT(name) "
                             "DO UPDATE SET calories=excluded.calories", values[:2])
            conn.execute("DELETE FROM diary_days WHERE day=?", (day,))
        return row_id

    def edit_food(self, row_id, name, calories, portions, meal):
        values = self.food_values(name, calories, portions, meal)
        with self.connection() as conn:
            conn.execute("DELETE FROM diary_days WHERE day=(SELECT day FROM foods WHERE id=?)", (row_id,))
            conn.execute("UPDATE foods SET name=?,calories=?,portions=?,meal=? WHERE id=?", (*values, row_id))

    def food_total(self, day):
        return round(sum(row["calories"] * row["portions"] for row in self.rows("foods", day)), 1)

    def add_workout(self, day, name, minutes):
        day = self.day(day)
        name = text(name, "Movement")
        minutes = number(minutes, "Minutes", 1, 600)
        if minutes != int(minutes):
            raise ValueError("Minutes must be a whole number.")
        with self.connection() as conn:
            return conn.execute("INSERT INTO workouts(day,name,minutes) VALUES (?,?,?)",
                                (day, name, int(minutes))).lastrowid

    def check_in(self, day, alcohol, mood, win):
        day = self.day(day)
        if alcohol not in (None, "free", "drank") or mood not in MOODS:
            raise ValueError("Choose a recognised check-in status.")
        win = text(win, "Small win", 1000, False)
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO checkins VALUES (?,?,?,?)", (day, alcohol, mood, win))

    def weigh(self, day, kg):
        day = self.day(day)
        kg = number(kg, "Weight", 10, 500)
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO weights VALUES (?,?)", (day, kg))

    def mark_complete(self, day, complete):
        day = self.day(day)
        if type(complete) is not bool:
            raise ValueError("Diary completeness must be true or false.")
        if complete and not self.rows("foods", day):
            raise ValueError("Log your food and drinks before marking this diary complete.")
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO diary_days VALUES (?,?)", (day, int(complete)))

    def delete(self, table, identifier):
        if table not in TABLES:
            raise ValueError("Unsupported diary table.")
        column = "id" if table in ("foods", "workouts", "favourites") else "day"
        with self.connection() as conn:
            if table == "foods":
                conn.execute("DELETE FROM diary_days WHERE day=(SELECT day FROM foods WHERE id=?)", (identifier,))
            conn.execute(f"DELETE FROM {table} WHERE {column}=?", (identifier,))

    def habits(self, end_day, days=7):
        end = date.fromisoformat(self.day(end_day))
        start = (end - timedelta(days=days - 1)).isoformat()
        checkins = [row for row in self.rows("checkins") if start <= row["day"] <= end_day]
        workouts = [row for row in self.rows("workouts") if start <= row["day"] <= end_day]
        complete = [row for row in self.rows("diary_days") if start <= row["day"] <= end_day and row["complete"]]
        return {"alcohol_free": sum(row["alcohol"] == "free" for row in checkins),
                "checkins": len(checkins), "movement_days": len({row["day"] for row in workouts}),
                "sessions": len(workouts), "minutes": sum(row["minutes"] for row in workouts),
                "complete_days": len(complete)}

    def export(self):
        # One read transaction keeps all tables and settings consistent.
        with self.connection() as conn:
            conn.execute("BEGIN")
            tables = {table: [dict(row) for row in conn.execute(f"SELECT * FROM {table}")] for table in TABLES}
            row = conn.execute("SELECT profile FROM settings WHERE id=1").fetchone()
            profile = json.loads(row[0]) if row else dict(DEFAULT_PROFILE)
        return json.dumps({"version": 1, "profile": profile, "tables": tables}, ensure_ascii=False, indent=2)

    def csv(self, table):
        rows = self.rows(table)
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                # Avoid spreadsheet formula evaluation of user-supplied text.
                writer.writerow({k: "'" + v if isinstance(v, str) and v[:1] in "=+-@\t\r" else v
                                 for k, v in row.items()})
        return output.getvalue().encode("utf-8-sig")

    def snapshot(self):
        folder = self.path.parent / "backups"
        folder.mkdir(exist_ok=True)
        target = folder / f"before-restore-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.db"
        with self.connection() as source, sqlite3.connect(target) as destination:
            source.backup(destination)
        return target

    def restore(self, payload):
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise ValueError("This is not a supported Steady Buddy backup.")
        profile = valid_profile(payload.get("profile"))
        tables = payload.get("tables")
        if not isinstance(tables, dict) or set(tables) != set(TABLES):
            raise ValueError("The backup has missing or unsupported diary tables.")
        validated = {}
        fields = {"foods": ("id", "day", "name", "calories", "portions", "meal"),
                  "workouts": ("id", "day", "name", "minutes"), "weights": ("day", "kg"),
                  "checkins": ("day", "alcohol", "mood", "win"),
                  "favourites": ("id", "name", "calories"), "diary_days": ("day", "complete")}
        for table in TABLES:
            rows = tables[table]
            if not isinstance(rows, list) or len(rows) > 100000:
                raise ValueError("The backup table is invalid or too large.")
            validated[table] = []
            seen = set()
            for row in rows:
                if not isinstance(row, dict) or set(row) != set(fields[table]):
                    raise ValueError(f"The backup contains an invalid {table} record.")
                row = dict(row)
                if "day" in row:
                    valid_day(row["day"], profile["timezone"])
                if "id" in row:
                    if type(row["id"]) is not int or row["id"] < 1:
                        raise ValueError("Backup IDs must be positive whole numbers.")
                unique = row.get("id", row.get("day"))
                if unique in seen:
                    raise ValueError("The backup contains duplicate diary records.")
                seen.add(unique)
                if table == "foods":
                    row["name"], row["calories"], row["portions"], row["meal"] = self.food_values(
                        row["name"], row["calories"], row["portions"], row["meal"])
                elif table == "workouts":
                    row["name"] = text(row["name"], "Movement")
                    minutes = number(row["minutes"], "Minutes", 1, 600)
                    if minutes != int(minutes):
                        raise ValueError("Workout minutes must be whole numbers.")
                    row["minutes"] = int(minutes)
                elif table == "weights":
                    row["kg"] = number(row["kg"], "Weight", 10, 500)
                elif table == "checkins":
                    if row["alcohol"] not in (None, "free", "drank") or row["mood"] not in MOODS:
                        raise ValueError("Invalid check-in in backup.")
                    row["win"] = text(row["win"], "Small win", 1000, False)
                elif table == "favourites":
                    row["name"] = text(row["name"], "Favourite")
                    row["calories"] = number(row["calories"], "Calories", 0, 10000)
                elif type(row["complete"]) is not int or row["complete"] not in (0, 1):
                    raise ValueError("Invalid diary completeness in backup.")
                validated[table].append(row)
        try:
            with self.connection() as conn:
                for table in TABLES:
                    conn.execute(f"DELETE FROM {table}")
                    columns = fields[table]
                    placeholders = ",".join("?" for _ in columns)
                    conn.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                                     [tuple(row[col] for col in columns) for row in validated[table]])
                conn.execute("INSERT OR REPLACE INTO settings VALUES (1,?)", (json.dumps(profile),))
        except sqlite3.IntegrityError:
            raise ValueError("The backup has conflicting records. Your existing diary was preserved.") from None
