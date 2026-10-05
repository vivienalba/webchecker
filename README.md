# Website Quality Checker

A Python website review workspace with a custom geometric interface for reviewing public websites before launch and after updates. No AI subscription or API key is required.

## Updated Streamlit entry point

`app.py` now displays the same branded web interface as `server.py`. Keep your existing Streamlit entry point set to `app.py` and upload the complete project contents, including `web/`, `sitecheck/`, and `streamlit_bridge.py`. Do not select `server.py` as a Streamlit entry point.

See **UPLOAD-STEPS.md** for the exact local check and GitHub upload steps. The browser transport has been checked in a protocol harness; a full launch with the real Streamlit runtime is still pending because dependency downloads were unavailable in the preparation environment. Test locally before updating the live site.

## Start on your Mac

Install Python 3.11 or newer, unzip this project, then open Terminal in the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://localhost:8501** in your browser. Keep Terminal open while using it. Enter a public URL to create a real report. Existing saved scans remain available under History. The redesigned interface does not generate fabricated results or scores.

For desktop/mobile screenshots and browser checks, install Chromium once:

```bash
python -m playwright install chromium
```

On Linux, browser OS dependencies may also be required: `python -m playwright install --with-deps chromium`.

## Use it

1. Enter a public website URL and confirm permission to review it.
2. Choose a page limit and checks. Start with one page; larger scans take longer.
3. Open **Findings** to review evidence and suggested actions. Set owners, deadlines, launch blockers and intentional exceptions.
4. Open **Pages & Previews** for previews, connections, social metadata, resources and guided manual reviews.
5. Use **Compare scans** from History after saving a second scan. Disappearing issues are labeled "not seen", not automatically "fixed".
6. Export a PDF, CSV or archive under **Reports**. The archive includes checklists, screenshots and issue cards.

See **FEATURES.md** for the exact implementation and limits of every proposed feature. Some findings require manual review; the app does not certify a website as accessible, secure, compliant or ready to launch.

## Recurring scans

Save a schedule in the app, then run this in a second terminal with the same virtual environment and project directory:

```bash
python worker.py
```

The worker must remain running. Closing your laptop or shutting down the worker pauses scheduling. Notifications appear inside the workspace; no email, Slack or other outbound messaging is configured. Schedules are not created until you choose to save one. To process at most one due job and exit, run `python worker.py --once`.

## Storage and hosting

Scan history, reviews, schedules, page text and screenshots are stored in `data/`. Back up this folder if needed. Use `QUALITY_DATA_DIR` to select a persistent storage location. Do not commit `data/`, passwords or scanned customer content to GitHub.

The app binds to `127.0.0.1` by default. It is a private single-workspace tool, not a multi-tenant SaaS product. An optional `QUALITY_APP_PASSWORD` environment variable adds a shared password gate. It is not a substitute for a production authentication layer, rate limiting, TLS and per-user authorization. Anyone admitted to the same workspace can see its data.

The branded interface now runs through **app.py** on Streamlit, using the bundled frontend and the existing scanner APIs. The standalone server remains available through `python server.py`. The old layout is retained as `app_legacy.py`. Browser previews require Chromium; schedules require an always-on worker. No hosting deployment has been created for you.

Before publishing a public service, configure authentication and infrastructure resource controls, define retention/deletion and adapt the app's data/use notice to the actual operator and hosting setup. The package adds no billing, analytics, advertising or external AI.

## Scan boundaries

- Public HTTP/HTTPS pages on standard ports only. Private, loopback, reserved and metadata addresses are blocked. DNS results are pinned for HTTP connections and every redirect is checked.
- Source crawling follows same-origin, query-free links, with a maximum of 30 HTML pages. Link destinations and resources may be on other public hosts.
- Maximum 500 HTTP requests, 600 seconds for the HTTP transport, 5 MB per response and 50 MB total downloaded by the transport. Defaults are smaller. Browser rendering has additional per-page timeouts.
- robots.txt restrictions are respected. If robots.txt cannot be verified, the destination is left unverified.
- No account login, form submission, purchase, email, text message or phone call. Browser write requests, service workers, WebSockets and popup windows are blocked.
- Blocked requests, unavailable assets and scan limits produce partial coverage. JavaScript-heavy sites may render incompletely.
- Browser source and computed-style heuristics can have false positives. Contrast checks cover simple solid backgrounds; focus and form behavior need manual review.
- Timings are observations from the scanning machine. They are not Lighthouse scores or Core Web Vitals.
- The browser is not a sandbox for hostile sites. For public hosting, isolate the scanner and browser in restricted containers with external network controls.

## Developer checks

```bash
python -m pip install pytest
python -m pytest -q
```

Core modules: `network.py` (bounded transport), `scanner.py` (HTML checks), `browser.py` (optional rendering), `storage.py` (SQLite), `reports.py` (exports). `worker.py` handles schedules. Unit tests use offline fixtures; they do not contact real websites.

Official implementation references: [Streamlit app testing](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [Playwright routing](https://playwright.dev/python/docs/api/class-route), [Playwright browser contexts](https://playwright.dev/python/docs/api/class-browser).

## Redesign / v2

The new interface uses locally bundled Open Sauce and Space Mono fonts, the four-color indigo/periwinkle/white/black palette, and original SVG cube geometry. Anime.js v4 implements scoped entrances, restrained press feedback, scan activity, result count reveals, filters, panels and confirmations. Reduced-motion preferences disable nonessential motion.

**Important:** the backend has no validated 0–100 quality scoring model. The interface preserves evidence-based result labels and displays verified destinations rather than inventing a score or severity rating.

The JavaScript bundle is included: **Node/npm are not required to run the app.** To edit and rebuild frontend source, run `npm install` followed by `npm run build` in the project folder. Fonts and library licenses are in `web/assets/` and `THIRD_PARTY.md`.

On macOS, launch the redesigned **Streamlit** version through `bash Start.command` (port 8503). Use `bash Start-standalone.command` for the standalone server. If Terminal says it is not executable, run `chmod +x Start.command`, then double-click it. Browser installation remains a separate optional step.
