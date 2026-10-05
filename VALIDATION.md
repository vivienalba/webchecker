# Scrollbar appearance update — October 5, 2026

Hidden scrollbar chrome on the page and settings panel using scrollbar-width and WebKit scrollbar rules. Removed the reserved scrollbar gutter. Existing overflow-y:auto, focusability, and scrolling transport remain unchanged. Updated the stylesheet URL to avoid cached CSS. No live-browser verification was available for this CSS-only update.

---

# Scrolling correction — October 5, 2026

Added an internal scroll region for the header, main content, and footer when the app is embedded in Streamlit. The settings dialog and notifications stay outside that region. Enabled vertical scrolling in the settings dialog and bumped the changed asset URLs to avoid old cached CSS/JavaScript.

Checked JavaScript syntax and HTML structure. The scanner/API files are unchanged. Browser rendering remains unverified in this environment because a browser binary and full Streamlit runtime are unavailable. Confirm scrolling in the running Mac or hosted app.

---

# Streamlit compatibility update — October 5, 2026

The new `app.py` connects the bundled interface to the original API handlers. The scanner, server handlers, worker, and storage modules are byte-for-byte unchanged. The old Streamlit file is preserved as `app_legacy.py`. CSS changed only to make local font URLs work in a component; the original design is preserved.

Verified in this preparation environment:
- Python syntax, JavaScript syntax, and launcher shell syntax.
- Six offline API bridge integration tests: boot/settings persistence; password isolation between sessions; API path and consent validation; a job with an explicitly substituted offline scan fixture; real PDF/CSV/ZIP/Markdown generation; and image bytes plus artifact path validation.
- A Node VM protocol harness: component readiness, sender validation, queued requests, duplicate response handling, JSON and error responses, binary download responses, image hydration/cache, asset passthrough, frame sizing, and standalone behavior.

Limits of verification:
- Streamlit, Beautiful Soup, certifi, and a Chromium binary were unavailable. Dependency installation timed out. No live scan, actual Streamlit launch, browser rendering, desktop/mobile screenshot inspection, or Community Cloud deployment was completed.
- Offline tests used inert import stand-ins for the missing Beautiful Soup and certifi modules. Calling those stand-ins raises immediately. They are not included in the application. The scan-job test explicitly substitutes a fixture for the scan operation; report generation and storage use the real implementations.
- Follow UPLOAD-STEPS.md to test the actual Streamlit app on the Mac before updating the live repository.

The earlier validation notes below describe the original package, not verification of this compatibility update.

---

# Validation of the redesigned build

- 39 automated tests passed across the existing scanner, storage, legacy UI and new HTTP API. Covered permission/URL validation, unsafe addresses, redirects, persisted reviews/checklists, comparison, exports, origin protection and authentication.
- Headless Chromium completed the new interface flow: scan settings, actual fixture-backed scanner progress, findings, severity/search filters, empty filtered results, review persistence, manual checklist, verified destinations, PDF download, history and comparisons.
- Mobile finding selection and back navigation passed. Both locked font families loaded. No JavaScript page errors were observed.
- Stress checks covered 105 findings with pagination, long URLs and descriptions, escaped markup, zero findings, missing reports, invalid URLs, repeated drawer dismissal with Escape and restored keyboard focus.
- No document overflow at 320, 390, 768, 1024 and 1440 pixels. Report tabs and technical tables scroll inside their own containers where appropriate.
- Reduced-motion emulation showed no running decorative animation on the initial screen.
- Landing, scanning, results and mobile screenshots were inspected. A PDF first page was rendered and visually checked for the branded fonts, palette and aligned metrics.

## Boundaries

Browser UI tests used controlled, explicitly fictional fixtures, with the real scanner behind the test API. Test servers and populated fixture databases are not included in the shipped workspace. Fresh installations contain no fabricated website results.

Live public-site network audits and Chromium-assisted inspection of third-party websites were not verified in this environment. Browser-dependent scanner features still require Chromium installation. The existing browser-unavailable handling is covered by tests.

Long-running deployed schedules and public multi-user hosting were not tested. This remains a private single-workspace application. There is no validated numerical scoring model; the interface displays observed findings and coverage rather than inventing scores.

Connection diagnostic update: robots.txt transport/TLS failures retain their underlying reason; explicit disallow rules stay distinct. Missing robots.txt (404) remains allowed. TLS supplements system trust with certifi and retains certificate/hostname verification. Six regression cases cover these behaviors.

Motion update: completed-work telemetry drives one shared bar/cube progress value; 100% is reported only after saving. Analysis tab transitions preserve the summary DOM. Desktop totals are centered. Verified with real-scanner fixtures, synchronized bar/cube checks, no continuous scan loops, repeated navigation, mobile layout, and reduced motion.
