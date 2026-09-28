import streamlit as st

from buddy.foods import FOODS
from buddy.store import MEALS
from buddy.ui import context, delete_record, diary_date, saved


def render():
    store, today, profile = context()
    st.header("Food, without the fuss.")
    st.caption("Log what you ate. An honest estimate is a useful start.")
    day = diary_date()
    options = {"Custom entry": ("", 0)}
    for row in store.rows("favourites"):
        options[f"Favourite: {row['name']}"] = (row["name"], row["calories"])
    for name, serving, calories in FOODS:
        options[f"{name} · {serving}"] = (name, calories)

    def fill_preset():
        name, calories = options[st.session_state["food_preset"]]
        st.session_state["food_name"] = name
        st.session_state["food_calories"] = float(calories)
        st.session_state["food_portions"] = 1.0

    st.selectbox("Start with a food or favourite", list(options), key="food_preset", on_change=fill_preset)
    st.caption("Food examples are illustrative estimates. Recipe, serving size and added oil change calories. Edit using your label or recipe.")
    with st.form("add_food"):
        name = st.text_input("Food or drink", max_chars=200, key="food_name", placeholder="e.g. Dal, rice and a roti")
        cols = st.columns(2)
        with cols[0]:
            calories = st.number_input("Calories per serving (kcal)", min_value=0.0, max_value=10000.0, step=5.0, key="food_calories")
        with cols[1]:
            portions = st.number_input("Servings", min_value=0.1, max_value=50.0, value=1.0, step=0.5, key="food_portions")
        meal = st.selectbox("Meal", MEALS, key="food_meal")
        favourite = st.checkbox("Save as a favourite", key="food_favourite")
        st.caption("Total calories = calories per serving × servings.")
        if st.form_submit_button("Add to diary", type="primary"):
            try:
                store.add_food(day, name, calories, portions, meal, favourite)
            except ValueError as exc:
                st.error(str(exc))
            else:
                saved("Meal saved. A little more awareness, a little less guesswork.")

    rows = store.rows("foods", day)
    st.subheader("Your diary")
    st.metric("Logged intake", f"{store.food_total(day):,.0f} kcal")
    if not rows:
        st.info("Your diary is empty for this date. Start with your next meal or drink.")
    for row in rows:
        with st.container(border=True):
            st.markdown(f"**{row['name']}**")
            st.caption(f"{row['meal']} · {row['portions']:g} serving(s) × {row['calories']:g} kcal = {row['calories'] * row['portions']:,.0f} kcal")
            with st.expander("Edit entry"):
                with st.form(f"edit_food_{row['id']}"):
                    new_name = st.text_input("Food or drink", row["name"], max_chars=200, key=f"edit_name_{row['id']}")
                    new_calories = st.number_input("Calories per serving (kcal)", 0.0, 10000.0, float(row["calories"]), key=f"edit_cal_{row['id']}")
                    new_portions = st.number_input("Servings", 0.1, 50.0, float(row["portions"]), key=f"edit_portion_{row['id']}")
                    new_meal = st.selectbox("Meal", MEALS, index=MEALS.index(row["meal"]), key=f"edit_meal_{row['id']}")
                    if st.form_submit_button("Save correction"):
                        try:
                            store.edit_food(row["id"], new_name, new_calories, new_portions, new_meal)
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            saved("Correction saved. This date is marked partial until you confirm it again.")
            delete_record(store, "foods", row["id"], "this meal", f"delete_food_{row['id']}")
    completed = store.rows("diary_days", day)
    with st.form(f"complete_day_{day}"):
        complete = st.checkbox("I've logged all food and drinks for this date", value=bool(completed and completed[0]["complete"]))
        if st.form_submit_button("Save diary status"):
            try:
                store.mark_complete(day, complete)
            except ValueError as exc:
                st.error(str(exc))
            else:
                saved("Diary status saved.")
    st.caption("An incomplete diary is never treated as a successful low-calorie day.")
    favourites = store.rows("favourites")
    if favourites:
        with st.expander("Manage favourites"):
            for row in favourites:
                st.caption(f"{row['name']} · {row['calories']:g} kcal per serving")
                delete_record(store, "favourites", row["id"], "this favourite", f"delete_fav_{row['id']}")
