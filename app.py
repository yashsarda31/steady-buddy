"""Personal diary, including installation support on Streamlit Community Cloud."""
import logging
import os
from pathlib import Path
import sqlite3

import streamlit as st

from buddy.store import Store, local_today
from buddy.hosting import cloud_hosting, cloud_store
from buddy.browser import install_controls, save_browser_backup
from buddy.design import apply_design, brand, footer
from buddy.scene import page_motion

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Steady Buddy · A little care, every day", page_icon=":material/spa:", layout="wide")
apply_design()
pages = [
    st.Page("app_pages/today.py", title="Today", icon=":material/wb_sunny:", default=True),
    st.Page("app_pages/food.py", title="Food", icon=":material/restaurant:", url_path="food"),
    st.Page("app_pages/move.py", title="Move", icon=":material/directions_walk:", url_path="move"),
    st.Page("app_pages/buddy.py", title="Buddy", icon=":material/favorite:", url_path="buddy"),
    st.Page("app_pages/progress.py", title="Progress", icon=":material/trending_up:", url_path="progress"),
    st.Page("app_pages/settings.py", title="Settings", icon=":material/tune:", url_path="settings"),
]
# Register routes before the browser handshake can stop the first run.
page = st.navigation(pages, position="hidden")
cloud = cloud_hosting(st.context.url)
with st.container(key="topbar"):
    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        brand()
    with right:
        browser = install_controls(cloud)
identity = st.session_state.get("_browser_identity") or browser.identity
if cloud and identity:
    st.session_state["_browser_identity"] = identity
if cloud and not identity:
    st.info("Opening your personal diary…")
    st.stop()
if cloud and isinstance(identity, dict) and identity.get("error"):
    st.error("Site storage is unavailable. Allow this site to save data, then reload. Your existing diary has been kept.")
    st.stop()
try:
    database = os.environ.get("BUDDY_DB_PATH", str(ROOT / "data" / "buddy.db"))
    store = cloud_store(Path(database).parent, identity) if cloud else Store(database)
    profile = store.profile()
except (sqlite3.Error, ValueError, OSError) as exc:
    logging.exception("Unable to open the personal diary")
    st.error(str(exc) if cloud and isinstance(exc, ValueError) else
             "Your diary couldn't be opened. Your data has been kept. Check the data folder or restore a backup after fixing access.")
    st.stop()

st.session_state["store"] = store
st.session_state["today"] = local_today(profile["timezone"])
st.session_state["profile"] = profile
st.session_state["cloud_hosting"] = cloud
if flash := st.session_state.pop("flash", None):
    st.success(flash)

# Streamlit suppresses its outer header in embedded views. Keep navigation in
# the actual diary, where it remains visible inside the installable PWA shell.
with st.container(horizontal=True, key="navigation"):
    for destination in pages:
        st.page_link(destination, label=destination.title, width="stretch")
try:
    page.run()
except (sqlite3.Error, OSError):
    logging.exception("Diary operation failed")
    st.error("That change couldn't be saved. Check available disk space and try again. Your existing diary is still here.")
footer()
if cloud:
    with st.container(key="recovery-footer"):
        save_browser_backup(store, identity["token"])
page_motion(page.title)
