# Verification · 28 September 2026

- **41 pytest tests passed:** durable diary records, portion arithmetic, validation, dates, atomic backup restore, completeness semantics, coaching, all six Streamlit views, cookie expiry, CSRF, origin checks, protected WebSockets, password rotation, secure HTTPS cookies and local host restrictions.
- **Ruff passed** with no findings.
- **9 real browser flows passed:** native Streamlit session; meal logging and refresh persistence; movement; craving support and a running/resettable timer; alcohol-free check-in; weigh-in chart; JSON download and restore through the actual file uploader; PWA manifest/service worker; offline recovery. Some checks group related steps.
- **3 private-access browser checks passed:** password login, authenticated native diary/WebSocket render, and Lock with protected reconnect.
- **24 layout checks passed:** Today, Food, Move, Buddy, Progress and Settings at 320, 390, 768 and 1440 pixels, with no horizontal document overflow.
- Chrome's installability check returned **zero errors**. The root-scope service worker activated, cached only public resources and served the honest offline screen.
- Browser page errors: **zero**.

All test data was stored in an isolated local test database. Test databases, downloads, screenshots, logs, backups, secrets and the local environment are excluded from the repository.

The supplied Docker/HTTPS hosting package has not been deployed. Physical Android/iPhone home-screen installation has not been verified; that requires the app at an HTTPS address on the device. Localhost installation works only on the computer running it. There are no background push notifications or offline diary writes.
