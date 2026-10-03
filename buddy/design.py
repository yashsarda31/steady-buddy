"""Shared visual language; native widgets retain their keyboard and form behavior."""
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


def apply_design():
    st.html(ROOT / "web" / "design.css")


def public_asset(relative):
    path = urlsplit(st.context.url or "").path
    prefix = path[:path.index("/~/+/") + 5] if "/~/+/" in path else "/streamlit/" if path.startswith("/streamlit/") else "/"
    return prefix + "app/static/" + relative


def brand():
    icon = public_asset("icons/buddy-mark.svg")
    st.html(f'''<div class="buddy-brand">
      <span class="brand-mark"><img src="{icon}" width="36" height="36" alt=""></span>
      <div><h1>Steady Buddy</h1><p>A little care, every day.</p></div>
    </div>''', width="content")


def eyebrow(text, number=None):
    prefix = f'<span class="section-number">{escape(str(number))}</span>' if number else ""
    st.html(f'<div class="eyebrow">{prefix}{escape(text)}</div>')


def page_heading(section, title, subtitle):
    with st.container(key="page-heading"):
        eyebrow(section)
        st.header(title)
        st.caption(subtitle)


def empty_state(title, body, symbol="sprout"):
    filename = {"food": "empty-food.svg", "move": "empty-move.svg"}.get(symbol, "buddy-mark.svg")
    icon = public_asset("icons/" + filename)
    st.html(f'''<div class="empty-state"><img src="{icon}" alt="" width="45" height="45"><strong>{escape(title)}</strong>
        <p>{escape(body)}</p></div>''')


def habit_strip(week):
    st.html(f'''<div class="habit-strip">
      <div><strong>{week['movement_days']}</strong><span>days with movement</span></div>
      <div><strong>{week['alcohol_free']}</strong><span>alcohol-free check-ins</span></div>
      <div><strong>{week['checkins']}</strong><span>moments to check in</span></div>
    </div>''')


def footer():
    st.html('''<div class="buddy-footer"><span class="footer-sprout" aria-hidden="true">✳</span>
      Your pace is your pace. Showing up counts.<span class="footer-label">SMALL STEPS, REAL LIFE</span></div>''')
