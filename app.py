"""Streamlit UI entry point. Launch run.py for PWA support."""
import logging
import os
from pathlib import Path
import sqlite3

import streamlit as st

from buddy.store import Store, local_today

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Steady Buddy", page_icon=":material/spa:", layout="centered")
try:
    store = Store(os.environ.get("BUDDY_DB_PATH", str(ROOT / "data" / "buddy.db")))
    profile = store.profile()
except (sqlite3.Error, ValueError, OSError):
    logging.exception("Unable to open the personal diary")
    st.error("Your diary couldn't be opened. Your data has been kept. Check the data folder or restore a backup after fixing access.")
    st.stop()

st.session_state["store"] = store
st.session_state["today"] = local_today(profile["timezone"])
st.session_state["profile"] = profile
st.title("Steady Buddy")
st.caption("Small steps. More patience. A healthier you.")
if flash := st.session_state.pop("flash", None):
    st.success(flash)

pages = [
    st.Page("app_pages/today.py", title="Today", icon=":material/wb_sunny:", default=True),
    st.Page("app_pages/food.py", title="Food", icon=":material/restaurant:", url_path="food"),
    st.Page("app_pages/move.py", title="Move", icon=":material/directions_walk:", url_path="move"),
    st.Page("app_pages/buddy.py", title="Buddy", icon=":material/favorite:", url_path="buddy"),
    st.Page("app_pages/progress.py", title="Progress", icon=":material/trending_up:", url_path="progress"),
    st.Page("app_pages/settings.py", title="Settings", icon=":material/tune:", url_path="settings"),
]
page = st.navigation(pages, position="hidden")
# Streamlit suppresses its outer header in embedded views. Keep navigation in
# the actual diary, where it remains visible inside the installable PWA shell.
with st.container(horizontal=True):
    for destination in pages:
        st.page_link(destination, label=destination.title, width="content")
try:
    page.run()
except (sqlite3.Error, OSError):
    logging.exception("Diary operation failed")
    st.error("That change couldn't be saved. Check available disk space and try again. Your existing diary is still here.")
st.space("small")
st.caption("Your pace is your pace. Showing up counts.")
