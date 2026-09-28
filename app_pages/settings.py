import json
import os
from zoneinfo import available_timezones

import streamlit as st

from buddy.ui import context, saved

store, today, profile = context()
st.header("Make this feel like yours.")
with st.form("profile_preferences"):
    name = st.text_input("What should I call you?", value=profile["name"], max_chars=60, key="profile_name")
    reason = st.text_area("Your reason for showing up", value=profile["reason"], max_chars=400, key="profile_reason")
    timezones = sorted(available_timezones())
    timezone = st.selectbox("Your timezone", timezones, index=timezones.index(profile["timezone"]), key="profile_timezone")
    sessions = st.number_input("Your movement sessions per week", min_value=1, max_value=14,
                               value=profile["weekly_sessions"], key="profile_sessions")
    use_reference = st.checkbox("Show my own daily calorie reference", value=profile["calorie_target"] is not None,
                                key="profile_use_target")
    target = st.number_input("Your daily calorie reference (kcal)", min_value=100.0, max_value=10000.0,
                             value=float(profile["calorie_target"] or 2000), step=50.0, key="profile_target")
    st.caption("Optional: use a reference suited to you, ideally agreed with a qualified professional. The app doesn't calculate or prescribe a weight-loss diet.")
    if st.form_submit_button("Save my preferences", type="primary"):
        try:
            store.save_profile({"name": name, "reason": reason, "timezone": timezone,
                                "weekly_sessions": sessions, "calorie_target": target if use_reference else None})
        except ValueError as exc:
            st.error(str(exc))
        else:
            saved("Preferences saved. We'll take this at your pace.")

st.subheader("Your data belongs to you")
st.caption("Saved in a private SQLite file on the computer or server running this app. Refreshes and restarts keep your diary. There is no analytics service or AI upload.")
st.download_button("Download full backup", data=store.export(), file_name=f"steady-buddy-{today}.json",
                   mime="application/json", icon=":material/download:")
with st.expander("Download spreadsheet-friendly history"):
    for table, label in [("foods", "Meals"), ("workouts", "Movement"), ("weights", "Weight"), ("checkins", "Check-ins")]:
        st.download_button(f"Download {label.lower()} CSV", store.csv(table), file_name=f"steady-buddy-{table}.csv",
                           mime="text/csv", key=f"csv_{table}")
with st.expander("Restore a backup"):
    st.caption("Restoring replaces this diary with your backup. A safety copy of the existing database is saved in data/backups first.")
    upload = st.file_uploader("Choose a Steady Buddy JSON backup", type="json", key="backup_upload")
    confirm = st.checkbox("Replace my current diary with this backup", key="restore_confirm")
    if st.button("Restore backup", disabled=upload is None or not confirm, key="restore_backup"):
        try:
            if upload.size > 10 * 1024 * 1024:
                raise ValueError("Choose a backup smaller than 10 MB.")
            payload = json.loads(upload.getvalue().decode("utf-8"))
            store.snapshot()
            store.restore(payload)
        except (ValueError, UnicodeDecodeError) as exc:
            st.error(f"Couldn't restore this backup: {exc}")
        else:
            # Clear widget values so restored settings, not old form state, are shown.
            for key in list(st.session_state):
                if key not in ("store", "today", "profile"):
                    del st.session_state[key]
            saved("Backup restored. Your previous diary has a safety copy on this server.")

st.subheader("Keep your buddy on your phone")
st.markdown("Open the app's main address in your phone browser. On **iPhone**, use Share → Add to Home Screen. On **Android**, use the browser's Install app option.")
st.caption("Phone installation needs HTTPS. Localhost installation works on this computer; a plain Wi-Fi IP address won't provide the secure connection needed on a phone. Logging needs a running server and a connection.")
st.caption("Reminders appear inside the app when you open it. Background push notifications are not enabled.")
with st.expander("Helpful resources"):
    st.link_button("Small steps for lasting habits · NIDDK", "https://www.niddk.nih.gov/health-information/diet-nutrition/changing-habits-better-health")
    st.link_button("Alcohol support and safety · NHS", "https://www.nhs.uk/live-well/alcohol-advice/alcohol-support/")
if os.environ.get("BUDDY_ACCESS_PASSWORD"):
    st.caption("This hosted diary uses a private access password. Use Lock in the app bar when you're finished on a shared device.")
