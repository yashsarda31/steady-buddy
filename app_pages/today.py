import streamlit as st

from buddy.coach import message
from buddy.design import eyebrow, habit_strip
from buddy.scene import garden_scene
from buddy.ui import checkin_form, context

store, today, profile = context()
day = today.isoformat()
with st.container(key="welcome"):
    greeting, garden = st.columns([1.2, 1], vertical_alignment="center")
    with greeting:
        st.html(f'<div class="welcome-date">{today.strftime("%A, %d %B")} · YOUR DAILY RESET</div>')
        st.header(f"You've got this, {profile['name']}.")
        st.html('<p class="welcome-note">You don’t need a perfect day.<br>Just a few <strong>kind choices.</strong></p>')
        st.html('<span class="welcome-pill"><i aria-hidden="true"></i> SMALL STEPS. A STEADIER YOU.</span>')
    with garden:
        garden_scene()

eyebrow("A little awareness", "01")
total = store.food_total(day)
movement = store.rows("workouts", day)
checkins = store.rows("checkins", day)
alcohol = checkins[0]["alcohol"] if checkins else None
with st.container(key="today-stats"):
    intake, activity, checkin = st.columns(3)
    with intake:
        st.metric("Calories logged", f"{total:,.0f} kcal", border=True)
    with activity:
        st.metric("Movement today", f"{sum(row['minutes'] for row in movement)} min", border=True)
    with checkin:
        st.metric("Alcohol check-in", {None: "Not recorded", "free": "Alcohol-free", "drank": "Recorded"}[alcohol], border=True)
if profile["calorie_target"]:
    reference = profile["calorie_target"]
    st.progress(min(total / reference, 1.0), text=f"{total:,.0f} of your {reference:,.0f} kcal daily reference")
    st.caption("This is logged intake, not a measure of how much you should eat next. A partial diary may miss food or drinks.")

eyebrow("Your next small step", "02")
with st.container(key="next-steps"):
    food, move, buddy = st.columns(3)
    with food:
        st.page_link("app_pages/food.py", label="Log a meal", icon=":material/restaurant:")
        st.caption("A little less guesswork.")
    with move:
        st.page_link("app_pages/move.py", label="Make time to move", icon=":material/directions_walk:")
        st.caption("Five minutes is a start.")
    with buddy:
        st.page_link("app_pages/buddy.py", label="I need encouragement", icon=":material/favorite:")
        st.caption("Your corner of calm.")

with st.container(key="today-bottom"):
    reflection, journal = st.columns([1, 1.2], gap="medium")
    with reflection:
        with st.container(key="gentle-reminder"):
            eyebrow("A NOTE FROM YOUR BUDDY")
            st.subheader("Good things take a little time.")
            reminder = message("Impatient", profile["reason"])
            st.markdown(reminder["body"])
            st.caption(reminder["reason"])
        with st.container(key="week-card"):
            eyebrow("A WEEK OF SMALL STEPS")
            st.subheader("The last 7 days")
            habit_strip(store.habits(day))
            st.caption("Only recorded days count. A blank day is simply a blank day.")
    with journal:
        with st.container(key="checkin-card"):
            eyebrow("A moment for you", "03")
            st.subheader("How’s your day, really?")
            st.caption("There’s no right answer. Just yours.")
            checkin_form(store, day, "today")
