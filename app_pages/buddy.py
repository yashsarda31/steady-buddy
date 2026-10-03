import streamlit as st

from buddy.coach import MESSAGES, message
from buddy.design import eyebrow, page_heading
from buddy.scene import garden_scene
from buddy.timer import pause_timer
from buddy.ui import checkin_form, context, diary_date

store, today, profile = context()
page_heading("YOUR CORNER OF CALM", "I'm in your corner.", "A place to pause, find a little perspective, and begin again.")
with st.container(key="buddy-layout"):
    calm, support = st.columns([.9, 1.3], gap="medium")
    with calm:
        with st.container(key="buddy-choice"):
            eyebrow("LET’S FIND A SMALL NEXT STEP")
            situation = st.selectbox("What would help right now?", list(MESSAGES), key="buddy_situation")
            garden_scene(key="buddy_garden")
            st.caption("Take the time you need. You can start again as often as you like.")
    with support:
        response = message(situation, profile["reason"])
        with st.container(key="buddy-response"):
            st.subheader(response["title"])
            st.markdown(response["body"])
            st.info(response["action"], icon=":material/spa:")
            st.caption(response["reason"])
        if situation == "Want a drink":
            st.subheader("Pause before deciding")
            with st.container(key="buddy-pause"):
                pause_timer()
            st.markdown("**Make it easier:** keep an alcohol-free drink nearby, step away from the trigger, or call someone you trust.")
            st.warning("If you depend on alcohol, or get shaking, sweating or other withdrawal symptoms, seek medical help before stopping. Sudden withdrawal can be dangerous.")
            st.link_button("Alcohol support and safety", "https://www.nhs.uk/live-well/alcohol-advice/alcohol-support/")
with st.container(key="buddy-checkin"):
    eyebrow("A LITTLE REFLECTION")
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
