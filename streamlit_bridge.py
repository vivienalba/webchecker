"""Use the existing API through Streamlit without a second server or port."""
import base64
import io
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import server
from sitecheck.storage import Store

def initialize_store(root):
    server.STORE = Store(os.environ.get("QUALITY_DATA_DIR") or Path(root) / "data")
    return server.STORE

class _Handler(server.Handler):
    def __init__(self, path, body, cookie):
        self.path = path
        self.headers = {"Content-Length": str(len(body)), "Content-Type": "application/json",
                        "X-Requested-With": "WebsiteChecker", "Host": "streamlit-component", "Cookie": cookie}
        self.rfile = io.BytesIO(body)
        self.cookie = cookie
        self.response = None

    def send(self, status, body, ctype="application/json", filename=None, cookie=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.response = {"status": status, "content_type": ctype,
                         "body": base64.b64encode(body).decode("ascii"), "filename": filename}
        if cookie:
            # Credentials stay server-side in the individual Streamlit session.
            self.cookie = cookie.split(";", 1)[0]

def dispatch(request, cookie=""):
    request_id = request.get("id") if isinstance(request, dict) else None
    handler = _Handler("/api/health", b"", cookie)
    try:
        if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
            raise ValueError("Invalid request identifier.")
        path, method = request.get("path", ""), request.get("method", "GET")
        if not isinstance(path, str) or len(path) > 16384:
            raise ValueError("Invalid API path.")
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/api/") or parsed.fragment:
            raise ValueError("Only this app's API paths are available.")
        if method not in ("GET", "POST"):
            raise ValueError("Unsupported request method.")
        body = request.get("body") or ""
        if not isinstance(body, str):
            raise ValueError("Invalid request body.")
        body = body.encode("utf-8")
        if len(body) > 12_000_000:
            raise ValueError("Upload is too large. Use an image under 8 MB.")
        handler = _Handler(path, body, cookie)
        if method == "GET":
            handler.do_GET()
        else:
            handler.do_POST()
    except (ValueError, TypeError) as exc:
        handler.send(400, {"error": str(exc)})
    except Exception:
        handler.send(500, {"error": "This action could not finish. Please try again."})
    return {"id": request_id, **handler.response}, handler.cookie
