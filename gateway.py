"""One-process PWA host using Streamlit's official ASGI integration."""
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import hashlib
import hmac
from html import escape
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from starlette.datastructures import Headers
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
COOKIE = "steady_buddy_session"
SESSION_AGE = 7 * 86400
PUBLIC = {"/health", "/login", "/manifest.webmanifest", "/sw.js", "/offline.html", "/web.css", "/web.js"}


def same_origin(scope):
    headers = Headers(scope=scope)
    try:
        origin = urlsplit(headers.get("origin", ""))
        host = urlsplit(f"{scope['scheme']}://{headers.get('host', '')}")
        origin_port = origin.port or (443 if origin.scheme == "https" else 80)
        host_port = host.port or (443 if scope["scheme"] in ("https", "wss") else 80)
        return origin.scheme in ("http", "https") and origin.hostname == host.hostname and origin_port == host_port
    except ValueError:
        return False


class AccessMiddleware:
    """Protect both HTTP and WebSocket entry points; never cache diary responses."""
    def __init__(self, app, password=""):
        self.app = app
        self.password = password
        self.signer = make_signer(password)

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        path = scope["path"]
        public = path in PUBLIC or path.startswith("/icons/")
        headers = Headers(scope=scope)
        if scope["type"] == "websocket" and not same_origin(scope):
            return await send({"type": "websocket.close", "code": 1008})
        if not public:
            if self.password:
                request = Request({**scope, "type": "http"})
                authorised = valid_token(self.signer, request.cookies.get(COOKIE, ""))
            else:
                client = scope.get("client")
                authorised = bool(client and client[0] in ("127.0.0.1", "::1", "testclient"))
            if not authorised:
                if scope["type"] == "websocket":
                    return await send({"type": "websocket.close", "code": 1008})
                response = RedirectResponse("/login", status_code=303) if self.password else HTMLResponse(
                    "Private diary: remote access requires an access password and HTTPS.", status_code=403)
                return await response(scope, receive, send)
        # Browser mutations must originate from this app. Streamlit's own XSRF protection remains enabled.
        if scope["type"] == "http" and scope["method"] not in ("GET", "HEAD", "OPTIONS"):
            if headers.get("origin") and not same_origin(scope):
                return await JSONResponse({"error": "Request origin rejected"}, status_code=403)(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                extra = [(b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"same-origin"),
                         (b"x-frame-options", b"SAMEORIGIN")]
                if not public:
                    # Replace inherited cache policy so authenticated media can't be shared.
                    message["headers"] = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                    extra.append((b"cache-control", b"no-store"))
                message["headers"] = list(message.get("headers", [])) + extra
            await send(message)
        await self.app(scope, receive, secure_send)


def make_signer(password):
    # Password rotation invalidates sessions. No password is written to disk.
    key = hashlib.sha256((password + os.environ.get("BUDDY_SESSION_SECRET", "")).encode()).digest()
    return TimestampSigner(key, salt="steady-buddy-v1")


def valid_token(signer, token):
    try:
        return signer.unsign(token, max_age=SESSION_AGE) == b"private-buddy"
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return False


def create_app(mount_streamlit=True, password=None):
    password = os.environ.get("BUDDY_ACCESS_PASSWORD", "") if password is None else password
    if password and len(password) < 12:
        raise ValueError("BUDDY_ACCESS_PASSWORD must have at least 12 characters.")
    signer = make_signer(password)
    attempts = defaultdict(deque)
    if mount_streamlit:
        import streamlit as st
        streamlit_app = st.App(ROOT / "app.py")
        lifespan = streamlit_app.lifespan()
    else:
        @asynccontextmanager
        async def lifespan(app):
            yield
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(AccessMiddleware, password=password)
    if not password:
        # Reject DNS-rebinding hosts even when the browser connects over loopback.
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": "Steady Buddy"}

    @app.get("/")
    async def index():
        return FileResponse(WEB / "index.html", headers={"Content-Security-Policy":
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'"})

    @app.get("/manifest.webmanifest")
    async def manifest():
        return FileResponse(WEB / "manifest.webmanifest", media_type="application/manifest+json")

    @app.get("/sw.js")
    async def service_worker():
        return FileResponse(WEB / "sw.js", media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})

    @app.get("/offline.html")
    async def offline():
        return FileResponse(WEB / "offline.html")

    @app.get("/web.css")
    async def stylesheet():
        return FileResponse(WEB / "web.css", media_type="text/css")

    @app.get("/web.js")
    async def javascript():
        return FileResponse(WEB / "web.js", media_type="application/javascript")

    def login_page(token, error=""):
        return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1"><title>Unlock · Steady Buddy</title>
        <link rel="stylesheet" href="/web.css"><link rel="manifest" href="/manifest.webmanifest"></head>
        <body class="standalone"><main class="card"><img src="/icons/icon-192.png" width="64" height="64" alt="">
        <p class="eyebrow">YOUR PRIVATE SPACE</p><h1>Welcome back.</h1><p>A little care, one day at a time.</p>
        <p role="alert">{escape(error)}</p><form action="/login" method="post" target="_top">
        <input type="hidden" name="csrf" value="{escape(token)}">
        <label for="password">Your access password</label><input id="password" name="password" type="password"
        autocomplete="current-password" required maxlength="512"><button type="submit">Unlock my buddy</button>
        </form></main></body></html>"""

    @app.get("/login")
    async def login_get(request: Request):
        if not password:
            return RedirectResponse("/", status_code=303)
        token = signer.sign(secrets.token_urlsafe(24)).decode()
        response = HTMLResponse(login_page(token), headers={"Cache-Control": "no-store"})
        response.set_cookie("steady_csrf", token, max_age=900, httponly=True, samesite="strict", secure=request.url.scheme == "https")
        return response

    @app.post("/login")
    async def login_post(request: Request):
        if not password:
            return RedirectResponse("/", status_code=303)
        form = await request.form(max_fields=4)
        csrf = str(form.get("csrf", ""))
        cookie = request.cookies.get("steady_csrf", "")
        try:
            if not csrf or not hmac.compare_digest(csrf, cookie):
                raise BadSignature("CSRF token mismatch")
            signer.unsign(csrf, max_age=900)
        except (BadSignature, SignatureExpired):
            return HTMLResponse("Please reopen the login page and try again.", status_code=403,
                                headers={"Cache-Control": "no-store"})
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        # Bound this ephemeral rate-limit map; it is never saved or used for analytics.
        if len(attempts) > 1000:
            attempts.clear()
        queue = attempts[client]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= 5:
            return HTMLResponse("Please wait a minute before trying again.", status_code=429,
                                headers={"Retry-After": "60", "Cache-Control": "no-store"})
        submitted = str(form.get("password", ""))
        if not hmac.compare_digest(submitted.encode(), password.encode()):
            queue.append(now)
            return HTMLResponse(login_page(csrf, "That password didn't match. Try again."), status_code=401,
                                headers={"Cache-Control": "no-store"})
        queue.clear()
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(COOKIE, signer.sign("private-buddy").decode(), max_age=SESSION_AGE,
                            httponly=True, samesite="strict", secure=request.url.scheme == "https")
        response.delete_cookie("steady_csrf")
        return response

    @app.post("/lock")
    async def lock(request: Request):
        if not same_origin(request.scope):
            return JSONResponse({"error": "Request origin rejected"}, status_code=403)
        response = JSONResponse({"locked": True})
        response.delete_cookie(COOKIE)
        return response

    @app.get("/session")
    async def session():
        return {"password_enabled": bool(password)}

    app.mount("/icons", StaticFiles(directory=WEB / "icons"), name="icons")
    if mount_streamlit:
        app.mount("/streamlit", streamlit_app)
    return app
