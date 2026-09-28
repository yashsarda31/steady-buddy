"""Client-side pause timer: no blocking sleep, no background notifications."""
import streamlit as st
from streamlit.components.v2 import component

_timer = component(
    "steady_pause_timer",
    html="""
    <div><p role="timer" aria-label="Pause time remaining" id="clock">2:00</p>
    <button type="button" id="start">Start a two-minute pause</button>
    <button type="button" id="reset">Reset</button>
    <p aria-live="polite" id="message">Relax your shoulders. Take a slow breath.</p></div>
    """,
    css="""
    button {font: inherit; color: var(--st-text-color); background: var(--st-secondary-background-color);
    border: 1px solid var(--st-border-color); border-radius: 20px; padding: 12px 18px; margin: 0 8px 8px 0; cursor: pointer;}
    button:focus-visible {outline: 3px solid var(--st-primary-color); outline-offset: 2px;}
    #clock {font-size: 2.4rem; margin: 8px 0; font-variant-numeric: tabular-nums;}
    """,
    js="""
    export default function ({parentElement}) {
      const clock = parentElement.querySelector('#clock');
      const start = parentElement.querySelector('#start');
      const reset = parentElement.querySelector('#reset');
      const message = parentElement.querySelector('#message');
      let deadline = 0, interval = null;
      function stop() { clearInterval(interval); interval = null; }
      function tick() {
        const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        clock.textContent = Math.floor(remaining / 60) + ':' + String(remaining % 60).padStart(2,'0');
        if (!remaining) { stop(); start.disabled = false; start.textContent = 'Take another pause';
          message.textContent = 'Pause complete. Notice how you feel, then choose your next kind step.'; }
      }
      start.onclick = () => { if (interval) return; deadline = Date.now() + 120000;
        start.disabled = true; message.textContent = 'One slow breath at a time.'; tick(); interval = setInterval(tick, 250); };
      reset.onclick = () => { stop(); clock.textContent = '2:00'; start.disabled = false;
        start.textContent = 'Start a two-minute pause'; message.textContent = 'Relax your shoulders. Take a slow breath.'; };
      return () => { stop(); start.onclick = null; reset.onclick = null; };
    }
    """,
)


def pause_timer():
    _timer(key="pause_timer")
    st.caption("This pause is optional. It resets if you leave this page.")
