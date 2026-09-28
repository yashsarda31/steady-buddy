import json
import re

from fastapi import WebSocket
from fastapi.testclient import TestClient
from PIL import Image
import pytest
from starlette.websockets import WebSocketDisconnect

from gateway import COOKIE, ROOT, SESSION_AGE, create_app, make_signer, valid_token
from run import check_binding


def client(password=""):
    return TestClient(create_app(mount_streamlit=False, password=password), follow_redirects=False)


def login(browser, password):
    response = browser.get("/login")
    csrf = re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)
    return browser.post("/login", data={"password": password, "csrf": csrf}, headers={"Origin": str(browser.base_url).rstrip("/")})


def test_pwa_assets_and_private_cache_policy():
    with client() as browser:
        assert browser.get("/").status_code == 200
        assert browser.get("/").headers["cache-control"] == "no-store"
        manifest = browser.get("/manifest.webmanifest").json()
        assert manifest["display"] == "standalone" and manifest["start_url"] == "/"
        for icon in manifest["icons"]:
            response = browser.get(icon["src"])
            assert response.status_code == 200
            assert Image.open(ROOT / "web" / icon["src"].lstrip("/")).size == tuple(map(int, icon["sizes"].split("x")))
        assert browser.get("/sw.js").headers["service-worker-allowed"] == "/"
        assert "Offline entries aren't saved" in browser.get("/offline.html").text


def test_password_protects_shell_and_streamlit():
    with client("a-strong-test-password") as browser:
        assert browser.get("/").status_code == 303
        assert browser.get("/streamlit/").status_code == 303
        assert login(browser, "incorrect").status_code == 401
        assert login(browser, "a-strong-test-password").status_code == 303
        assert COOKIE in browser.cookies
        assert browser.get("/").status_code == 200
        assert browser.get("/session").json()["password_enabled"]
        assert browser.post("/lock", headers={"Origin": "http://testserver"}).status_code == 200
        assert browser.get("/").status_code == 303


def test_login_csrf_and_origin_are_enforced():
    with client("a-strong-test-password") as browser:
        assert browser.post("/login", data={"password": "a-strong-test-password"}).status_code == 403
        browser.get("/login")
        csrf = browser.cookies["steady_csrf"]
        assert browser.post("/login", data={"password": "a-strong-test-password", "csrf": csrf},
                            headers={"Origin": "https://evil.example"}).status_code == 403


def test_remote_binding_needs_password():
    check_binding("127.0.0.1", "")
    with pytest.raises(ValueError):
        check_binding("0.0.0.0", "")
    check_binding("0.0.0.0", "a-strong-test-password")
    with pytest.raises(ValueError):
        create_app(mount_streamlit=False, password="short")


def test_local_diary_rejects_untrusted_host():
    with client() as browser:
        assert browser.get("/", headers={"Host": "untrusted.example"}).status_code == 400


def test_token_rejects_tampering_and_rotation():
    signer = make_signer("a-strong-test-password")
    token = signer.sign("private-buddy").decode()
    assert valid_token(signer, token)
    assert not valid_token(signer, token + "changed")
    assert not valid_token(make_signer("a-different-test-password"), token)


def test_session_expiry_and_secure_https_cookie(monkeypatch):
    signer = make_signer("a-strong-test-password")
    real_now = signer.get_timestamp()
    monkeypatch.setattr(signer, "get_timestamp", lambda: real_now - SESSION_AGE - 1)
    token = signer.sign("private-buddy").decode()
    monkeypatch.setattr(signer, "get_timestamp", lambda: real_now)
    assert not valid_token(signer, token)
    with TestClient(create_app(mount_streamlit=False, password="a-strong-test-password"),
                    base_url="https://testserver", follow_redirects=False) as browser:
        response = login(browser, "a-strong-test-password")
        session_cookie = next(cookie for cookie in response.headers.get_list("set-cookie") if cookie.startswith(COOKIE))
        assert "Secure" in session_cookie and "HttpOnly" in session_cookie and "SameSite=strict" in session_cookie


def test_websocket_requires_login_and_same_origin():
    app = create_app(mount_streamlit=False, password="a-strong-test-password")

    @app.websocket("/streamlit/echo")
    async def typed_echo(socket: WebSocket):
        await socket.accept()
        await socket.send_text("connected")
        await socket.close()

    with TestClient(app, follow_redirects=False) as browser:
        with pytest.raises(WebSocketDisconnect):
            with browser.websocket_connect("/streamlit/echo", headers={"Origin": "http://testserver"}):
                pass
        login(browser, "a-strong-test-password")
        with pytest.raises(WebSocketDisconnect):
            with browser.websocket_connect("/streamlit/echo", headers={"Origin": "https://evil.example"}):
                pass
        with browser.websocket_connect("/streamlit/echo", headers={"Origin": "http://testserver"}) as socket:
            assert socket.receive_text() == "connected"


def test_private_data_is_absent_from_service_worker_cache_list():
    source = (ROOT / "web" / "sw.js").read_text()
    assets = json.loads(re.search(r"const ASSETS = (\[.*?\]);", source).group(1).replace("'", '"'))
    assert all(not path.startswith(("/streamlit", "/session", "/login")) for path in assets)
