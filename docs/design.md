# Steady Buddy

Approved 2026-09-28. The user requested implementation without further questions.

A single-person, private Streamlit companion for sustainable habits. Friendly cream and forest-green mobile UI, six views: Today, Food, Move, Buddy, Progress, Settings. No external AI or nutrition service is required.

- Food: editable example serving estimates, custom foods, portions, meal categories, favourites, dated history, corrections and deletion. Intake totals never subtract exercise or claim that an incomplete diary is a calorie deficit. A daily calorie reference is optional and user supplied.
- Movement: small chosen actions, manual workout logs, a user-selected weekly session goal, rest days acknowledged. No exercise-to-food compensation.
- Buddy: situation-specific encouragement for impatience, low motivation, cravings and setbacks; a real browser countdown for a pause; daily mood, alcohol-free/drank/not-recorded status and a small win. Missing check-ins are never counted as alcohol-free days. No penalties for lapses.
- Progress: dated weight observations, seven-day trailing average of recorded measurements, observed habit counts, and diary completeness. No predicted weight-loss deadlines.
- Storage: independent local SQLite database, validated writes, atomic JSON restore, JSON/CSV downloads, explicit confirmation for deletion. Dates use the user's timezone, default Asia/Kolkata. No analytics or cloud uploads.
- PWA: same-origin FastAPI host mounting Streamlit's official ASGI application, a manifest with icons, installation instructions, service worker caching only public assets and an honest offline screen. Tracking needs a running server. Remote hosting requires HTTPS, persistent storage and an access password. Local-only binding is the default.
- Delivery: isolated Python environment, Windows launcher, container and hosting instructions. Automated storage, coaching, AppTest, gateway/auth and browser tests plus narrow-screen verification. The user later authorized publishing the source to a public GitHub repository. Live app hosting has not been requested.

Health copy supports modest habits rather than prescribing calorie targets. Alcohol support includes the NHS warning to get medical help before stopping if dependent or experiencing withdrawal. Resources: https://www.niddk.nih.gov/health-information/diet-nutrition/changing-habits-better-health and https://www.nhs.uk/live-well/alcohol-advice/alcohol-support/.
