from datetime import timedelta

import pandas as pd
import altair as alt
import streamlit as st

from buddy.coach import weight_trend
from buddy.ui import context, delete_record, diary_date, saved

store, today, profile = context()
st.header("Progress has more than one shape.")
st.markdown("Look for patterns across weeks. **Your effort counts before the scale changes.**")
week = store.habits(today.isoformat())
with st.container(horizontal=True):
    st.metric("Days with movement", week["movement_days"], border=True)
    st.metric("Alcohol-free check-ins", week["alcohol_free"], border=True)
    st.metric("Complete food diaries", week["complete_days"], border=True)
st.caption("Last 7 calendar days, including today. Only your recorded habits count.")

st.subheader("Weight, at your own pace")
st.caption("Weighing is optional. Save at most one measurement per date; saving again corrects that date.")
day = diary_date("Weigh-in date", key="weight_date")
with st.form("weighin"):
    weight = st.number_input("Weight (kg)", min_value=10.0, max_value=500.0, value=None, step=0.1,
                             placeholder="Enter your measurement", key="weight_kg")
    if st.form_submit_button("Save weigh-in", type="primary"):
        try:
            store.weigh(day, weight)
        except ValueError as exc:
            st.error(str(exc))
        else:
            saved("Weigh-in saved. One number is only one moment.")
weights = store.rows("weights")
if weights:
    points = pd.DataFrame(weight_trend(weights))
    points["Date"] = pd.to_datetime(points["Date"])
    chart = (alt.Chart(points).transform_fold(["Weight", "7-day average"], as_=["Series", "kg"])
             .mark_line(point=True).encode(x=alt.X("Date:T", title="Date"),
                                          y=alt.Y("kg:Q", scale=alt.Scale(zero=False), title="kg"),
                                          color="Series:N", tooltip=["Date:T", "Series:N", "kg:Q"]).properties(height=260))
    st.altair_chart(chart, width="stretch")
    latest = points.iloc[-1]
    st.caption(f"The latest average uses {int(latest['Measurements in window'])} recorded measurement(s) "
               "in the seven calendar days ending at the last weigh-in. Missing dates are not filled in.")
    with st.expander("Measurements and corrections"):
        st.dataframe(pd.DataFrame(weights), hide_index=True)
        selected = st.selectbox("Measurement to remove", [row["day"] for row in weights], key="remove_weight_day")
        delete_record(store, "weights", selected, "this weigh-in", "delete_weight")
else:
    st.info("Your trend will appear when you save a weigh-in. You can also focus entirely on habits.")

st.subheader("Your food diary over time")
start = (today - timedelta(days=29)).isoformat()
foods = [row for row in store.rows("foods") if start <= row["day"] <= today.isoformat()]
if foods:
    frame = pd.DataFrame(foods)
    frame["Logged calories"] = frame["calories"] * frame["portions"]
    daily = frame.groupby("day", as_index=False)["Logged calories"].sum()
    complete = {row["day"]: bool(row["complete"]) for row in store.rows("diary_days")}
    daily["Diary status"] = daily["day"].map(lambda day: "Complete" if complete.get(day) else "Partial")
    daily = daily.rename(columns={"day": "Date"})
    st.dataframe(daily, hide_index=True)
    st.caption("Last 30 days with food entries. Partial totals can miss meals, drinks and cooking oil; they don't prove a calorie deficit.")
else:
    st.caption("Once you log meals, recorded daily totals and completeness will appear here.")
with st.expander("Check-in history"):
    checkins = store.rows("checkins")
    if checkins:
        history = pd.DataFrame(checkins)
        history["alcohol"] = history["alcohol"].map({None: "Not recorded", "free": "Alcohol-free", "drank": "Had a drink"})
        st.dataframe(history, hide_index=True)
        selected = st.selectbox("Check-in to remove", [row["day"] for row in checkins], key="remove_checkin_day")
        delete_record(store, "checkins", selected, "this check-in", "delete_checkin")
    else:
        st.caption("Your check-ins will appear here.")
