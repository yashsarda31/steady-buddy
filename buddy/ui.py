"""Shared native UI helpers."""
from datetime import date

import streamlit as st

from buddy.store import MOODS


def context():
    return st.session_state["store"], st.session_state["today"], st.session_state["profile"]


def saved(message):
    st.session_state["flash"] = message
    st.rerun()


def diary_date(label="Diary date", key="diary_date"):
    today = st.session_state["today"]
    return st.date_input(label, value=today, min_value=date(2000, 1, 1), max_value=today, key=key).isoformat()


def checkin_form(store, day, key="checkin"):
    rows = store.rows("checkins", day)
    row = rows[0] if rows else {"alcohol": None, "mood": "Okay", "win": ""}
    labels = {None: "Not recorded", "free": "Alcohol-free", "drank": "I had a drink"}
    reverse = {label: status for status, label in labels.items()}
    with st.form(f"{key}_{day}"):
        mood = st.selectbox("How are you feeling?", MOODS, index=MOODS.index(row["mood"]), key=f"{key}_mood_{day}")
        alcohol = st.selectbox("Alcohol check-in", list(reverse), index=list(labels).index(row["alcohol"]),
                               help="A check-in describes the day so far. You can update it later.", key=f"{key}_alcohol_{day}")
        win = st.text_area("One small win", value=row["win"], max_chars=1000, placeholder="I logged lunch. I took a walk. I was kind to myself.", key=f"{key}_win_{day}")
        if st.form_submit_button("Save check-in", type="primary"):
            store.check_in(day, reverse[alcohol], mood, win)
            saved("Check-in saved. Honest days count, too.")


def delete_record(store, table, identifier, label, key):
    with st.popover("Remove", icon=":material/delete:"):
        st.caption(f"Remove {label} from your diary?")
        if st.button("Confirm removal", key=key):
            store.delete(table, identifier)
            saved("Entry removed.")
