import streamlit as st

from buddy.coach import message
from buddy.ui import checkin_form, context

store, today, profile = context()
day = today.isoformat()
st.badge(today.strftime("%A, %d %B"), icon=":material/calendar_today:", color="green")
st.header(f"You've got this, {profile['name']}.")
st.markdown("You don't need a perfect day. **Just a few kind choices.**")
with st.container(border=True):
    st.subheader("Today's gentle reminder")
    reminder = message("Impatient", profile["reason"])
    st.markdown(reminder["body"])
    st.caption(reminder["reason"])

total = store.food_total(day)
movement = store.rows("workouts", day)
checkins = store.rows("checkins", day)
alcohol = checkins[0]["alcohol"] if checkins else None
with st.container(horizontal=True):
    st.metric("Calories logged", f"{total:,.0f} kcal", border=True)
    st.metric("Movement today", f"{sum(row['minutes'] for row in movement)} min", border=True)
    st.metric("Alcohol check-in", {None: "Not recorded", "free": "Alcohol-free", "drank": "Recorded"}[alcohol], border=True)
if profile["calorie_target"]:
    reference = profile["calorie_target"]
    st.progress(min(total / reference, 1.0), text=f"{total:,.0f} of your {reference:,.0f} kcal daily reference")
    st.caption("This is logged intake, not a measure of how much you should eat next. A partial diary may miss food or drinks.")

st.subheader("Your next small step")
with st.container(horizontal=True):
    st.page_link("app_pages/food.py", label="Log a meal", icon=":material/restaurant:")
    st.page_link("app_pages/move.py", label="Make time to move", icon=":material/directions_walk:")
    st.page_link("app_pages/buddy.py", label="I need encouragement", icon=":material/favorite:")

st.subheader("A moment for you")
checkin_form(store, day, "today")
week = store.habits(day)
with st.container(border=True):
    st.subheader("The last 7 days")
    st.markdown(f"**{week['movement_days']}** days with movement · **{week['alcohol_free']}** recorded alcohol-free days · **{week['checkins']}** check-ins")
    st.caption("Only recorded days count. A blank day is simply a blank day.")
