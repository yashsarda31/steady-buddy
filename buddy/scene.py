"""Inline v2 visual enhancements; diary operations never depend on JavaScript."""
from pathlib import Path

from streamlit.components.v2 import component

ROOT = Path(__file__).resolve().parents[1]

_garden = component(
    "steady_pebble_garden",
    html=(ROOT / "web" / "garden.html").read_text(encoding="utf-8"),
    css=(ROOT / "web" / "garden.css").read_text(encoding="utf-8"),
    js=(ROOT / "web" / "garden.js").read_text(encoding="utf-8"),
)

_motion = component(
    "steady_page_motion",
    html='<span aria-hidden="true"></span>',
    js=(ROOT / "web" / "motion.js").read_text(encoding="utf-8"),
)


def garden_scene(key="garden"):
    _garden(key=key)


def page_motion(route):
    _motion(key="page_motion", data={"route": route}, height=0)
