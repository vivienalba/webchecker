# Latest update: hidden scrollbar

The page and settings panel now hide the visible scrollbar while retaining mouse wheel, trackpad, touch, and keyboard scrolling. Replace the existing `web` folder with the one in this ZIP, restart the app, and refresh the browser. The changed files for this specific update are `web/style.css` and `web/index.html`.

# Scrolling fix for the latest Streamlit package

If you already installed the preceding Streamlit update, replace its entire `web` folder with the `web` folder in this ZIP. The changed files are `web/index.html`, `web/style.css`, and `web/streamlit-bridge.js`. Restart the running app and refresh the browser. Your Python files and saved scan data do not need changing for this scrolling fix.

On a Mac, stop the app with Control+C in its Terminal, then run `bash Start.command` again from the existing project folder. In the browser, use Command+Shift+R if old assets still appear.

If the app is already online, upload those three changed files to the same `web` folder in the connected GitHub branch. If Streamlit still serves the earlier assets after the commit, use Manage app > menu > Reboot app.

Check that you can scroll down to the footer, reach long report content, and scroll inside Scan Settings. The existing installation and publishing steps follow.

---

# Put the new design on your existing Streamlit website

## 1. Check this updated package on your Mac

1. Unzip the updated ZIP into a new folder so it does not mix with an older copy.
2. Open Terminal, type `cd `, drag the extracted `WebsiteChecker-NoArrows` folder into Terminal, and press Enter.
3. If an older app is running on port 8503, press Control+C in its Terminal first.
4. Run `bash Start.command`.
5. Open http://localhost:8503. Check for **Know your website. Inside out.**
6. Open Scan Settings, History, and Reports. Try a small scan of a public website you own or have permission to review, then download its PDF.

This launcher now starts Streamlit using `app.py`. The interface, fonts, animation bundle, and no-arrow styling are the ones in the `web` folder. The scanner backend remains in `server.py` and `sitecheck/`.

A full run with Streamlit was not possible in the preparation environment because its Python dependencies could not be downloaded. Finish this local check before changing the live site. If a startup error appears, retain the error text and the existing live version.

## 2. Update the GitHub repository connected to Streamlit

1. Open the GitHub repository used by `websiteqc.streamlit.app`.
2. Open the folder that currently contains its `app.py`.
3. Choose **Add file > Upload files**.
4. Upload all the files and folders INSIDE the newly extracted project folder. Do not upload the ZIP or add an extra parent folder around the files.
5. Include `app.py`, `streamlit_bridge.py`, `server.py`, `requirements.txt`, the entire `web` folder (with its assets), and the entire `sitecheck` folder. Include the other supplied project files too. Do not upload `.venv`, `data`, or secret/password files from your Mac.
6. If Finder hides `.streamlit`, press Command+Shift+Period to show it and include the supplied `.streamlit/config.toml` too. Never include an existing `.streamlit/secrets.toml`.
7. Commit the changes to the branch your Streamlit app uses. Keep the main file path pointing to `app.py` in its existing folder.
8. Return to your Streamlit site and wait for the update. Reboot from **Manage app** only if it remains on the old version after the repository update finishes.
9. Check the heading again and repeat the small scan and PDF check.

## Hosting notes

This remains one shared workspace: people admitted to the app can see its saved scans. Existing access restrictions and an optional `QUALITY_APP_PASSWORD` remain supported.

Streamlit Community Cloud does not guarantee persistent local storage. Export needed reports; local scan history can be lost on app restarts/redeployments. Recurring scans still require the separate worker and an always-running host. Optional browser previews still require Chromium and its OS dependencies; the ordinary HTML scan does not require it.

`Start-standalone.command` retains the original `server.py` launch. `app_legacy.py` retains the previous Streamlit layout for reference.
