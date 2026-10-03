import streamlit as st

from buddy.design import empty_state, eyebrow, page_heading
from buddy.ui import context, delete_record, diary_date, saved

store, today, profile = context()
page_heading("MOVEMENT & REST", "Start small. Keep showing up.", "Movement is care. You don’t need to earn your meals.")
with st.container(key="move-layout"):
    plan_column, log_column = st.columns([1, 1.12], gap="medium")
    with plan_column:
        with st.container(key="move-plan"):
            eyebrow("MEET YOURSELF WHERE YOU ARE", "01")
            plan = st.selectbox("What feels manageable today?", ["A gentle walk", "Some stretching", "My own workout", "A rest day"], key="move_plan")
            with st.container():
                plans = {"A gentle walk": ("Just five minutes to begin.", "Find a comfortable pace. You can finish after five minutes or keep going if you feel good."),
                         "Some stretching": ("Make a little room to breathe.", "Try a few gentle, comfortable stretches. Avoid movements that hurt."),
                         "My own workout": ("Make the first step easy.", "Choose the workout you enjoy and scale it to your energy today."),
                         "A rest day": ("Rest belongs in the plan.", "Recovery supports consistency. You can return when you're ready.")}
                st.subheader(plans[plan][0])
                st.markdown(plans[plan][1])
        with st.container(key="move-week"):
            eyebrow("CONSISTENCY, AT YOUR PACE")
            st.subheader("A little movement adds up.")
            week = store.habits(today.isoformat())
            goal = profile["weekly_sessions"]
            st.progress(min(week["sessions"] / goal, 1.0), text=f"{week['sessions']} of your {goal} chosen sessions · last 7 days")
            st.caption("Your goal is editable in Settings. A session can be short; consistency doesn't require intensity.")
    with log_column:
        with st.container(key="move-tools"):
            eyebrow("MAKE A NOTE OF IT", "02")
            st.subheader("Log the movement you did")
            day = diary_date(key="move_date")
            with st.form("workout"):
                name = st.text_input("Movement", value="Walk", max_chars=200, key="workout_name")
                minutes = st.number_input("Minutes", min_value=1, max_value=600, value=10, key="workout_minutes")
                if st.form_submit_button("Save movement", type="primary"):
                    try:
                        store.add_workout(day, name, minutes)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        saved("Movement saved. You made time for yourself.")
        st.subheader("Recorded movement")
        if not store.rows("workouts", day):
            empty_state("Your next step starts here.", "A walk, a stretch, a workout. Log what you did when you’re ready.", "move")
        for row in store.rows("workouts", day):
            with st.container(border=True):
                st.markdown(f"**{row['name']}** · {row['minutes']} minutes")
                delete_record(store, "workouts", row["id"], "this movement entry", f"delete_workout_{row['id']}")
