"""Cloud diary selection and recovery, independent of Streamlit widgets."""
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from buddy.store import Store


def cloud_hosting(url):
    mode = os.environ.get("BUDDY_HOSTING", "auto")
    if mode != "auto":
        return mode == "cloud"
    host = urlsplit(url or "").hostname or ""
    return host.endswith(".streamlit.app")


def cloud_store(folder, browser):
    if not isinstance(browser, dict) or not re.fullmatch(r"[a-f0-9]{64}", str(browser.get("token", ""))):
        raise ValueError("Your browser diary could not be identified. Reload this page.")
    identifier = hashlib.sha256(browser["token"].encode()).hexdigest()
    path = Path(folder) / "devices" / f"{identifier}.db"
    missing = not path.exists()
    store = Store(path)
    backup = browser.get("backup")
    if missing and backup:
        try:
            if not isinstance(backup, str) or len(backup.encode("utf-8")) > 10 * 1024 * 1024:
                raise ValueError("The browser backup is too large.")
            store.restore(json.loads(backup))
        except ValueError:
            # Leave recovery retryable; never replace the browser copy with an empty diary.
            path.unlink(missing_ok=True)
            raise ValueError("Your browser backup couldn't be restored. Keep your downloaded backup and use Settings to restore it in another browser.") from None
    return store
