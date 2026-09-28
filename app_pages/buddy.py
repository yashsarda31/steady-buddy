import streamlit as st

from buddy.coach import MESSAGES, message
from buddy.timer import pause_timer
from buddy.ui import checkin_form, context, diary_date

store, today, profile = context()
st.header("I'm in your corner.")
st.caption("A calm place to reset. No judgment, no pressure to be perfect.")
situation = st.selectbox("What would help right now?", list(MESSAGES), key="buddy_situation")
response = message(situation, profile["reason"])
with st.container(border=True):
    st.subheader(response["title"])
    st.markdown(response["body"])
    st.info(response["action"], icon=":material/spa:")
    st.caption(response["reason"])
if situation == "Want a drink":
    st.subheader("Pause before deciding")
    pause_timer()
    st.markdown("**Make it easier:** keep an alcohol-free drink nearby, step away from the trigger, or call someone you trust.")
    st.warning("If you depend on alcohol, or get shaking, sweating or other withdrawal symptoms, seek medical help before stopping. Sudden withdrawal can be dangerous.")
    st.link_button("Alcohol support and safety", "https://www.nhs.uk/live-well/alcohol-advice/alcohol-support/")
st.subheader("Save a check-in")
day = diary_date(key="buddy_date")
checkin_form(store, day, "buddy")
with st.expander("Your recent small wins"):
    wins = [row for row in store.rows("checkins") if row["win"]][:14]
    if not wins:
        st.caption("Your first small win belongs here. It can be as simple as showing up today.")
    for row in wins:
        st.caption(row["day"])
        st.text(row["win"])
st.caption("These are supportive prompts, not AI chat or medical treatment.")
