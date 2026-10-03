"""Installation controls and browser recovery for normal Streamlit hosting."""
from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component

ROOT = Path(__file__).resolve().parents[1]

_install = component(
    "steady_browser",
    html="""
    <div class="steady-browser" id="controls"><button type="button" id="install">Install app</button>
    <p id="storage" role="status"></p>
    <div id="help" role="region" aria-label="Installation instructions" hidden><h3>Keep your buddy close.</h3>
    <p><strong>iPhone / iPad:</strong> Open in Safari, tap Share, then Add to Home Screen.</p>
    <p><strong>Android:</strong> Open in Chrome, tap the menu, then Install app or Add to Home Screen.</p>
    <p><strong>Computer:</strong> In Chrome or Edge, use the install icon in the address bar, or the browser menu to install this page as an app.</p>
    <p id="secure"></p><p>Your diary needs an internet connection. Installation does not enable offline logging or background reminders.</p>
    <button type="button" id="close">Got it</button></div></div>
    """,
    css="""
    .steady-browser {text-align: right;}
    .steady-browser button {font: 600 12px "DM Sans", sans-serif; color: #284c38; background: #f7f7f0;
      border: 1px solid #ccd7c3; border-radius: 30px; padding: 10px 17px; min-height: 42px; cursor: pointer; white-space: nowrap;}
    .steady-browser button:hover {background: #e5ecdc;}
    .steady-browser button:focus-visible {outline: 3px solid var(--st-primary-color); outline-offset: 2px;}
    .steady-browser p {font-size: .8rem; line-height: 1.6;} .steady-browser #storage {display: none;}
    .steady-browser #help {position:fixed; top:80px; right:20px; width:min(90vw,420px); box-sizing:border-box;
      max-height:75vh; overflow:auto; z-index:999999; text-align:left; padding: 22px; background:#fffefa;
      border: 1px solid #dce2d7; border-radius: 22px; box-shadow:0 18px 70px #24473330;}
    .steady-browser [hidden] {display: none !important;}
    """,
    js=(ROOT / "web" / "streamlit-install.js").read_text(encoding="utf-8"),
)

_backup = component(
    "steady_browser_backup",
    html="""<p role="status" id="status"></p>""",
    css="""
    #status {
      font: 10px/1.6 'DM Sans', sans-serif;
      color:#586b60;
      margin:0;
    }
    """,
    js="""
    export default function ({parentElement, data}) {
      const status = parentElement.querySelector('#status');
      try {
        const record = JSON.parse(localStorage.getItem('steady-buddy-diary-v1') || 'null');
        if (!record || record.token !== data.token) throw new Error('Browser identity changed');
        localStorage.setItem('steady-buddy-diary-v1', JSON.stringify({token: data.token, backup: data.backup}));
        status.textContent = 'Recovery copy saved in this browser. Download a backup to use another device.';
      } catch {
        status.textContent = 'Browser recovery copy could not be saved. Download a full backup in Settings before closing the app.';
      }
    }
    """,
)


def install_controls(cloud=False):
    return _install(key="browser_diary", data={"cloud": cloud, "identity_ready": "_browser_identity" in st.session_state},
                    on_identity_change=lambda: None)


def save_browser_backup(store, token):
    _backup(key="browser_backup", data={"token": token, "backup": store.export()})
