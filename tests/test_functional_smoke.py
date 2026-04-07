import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts.functional_smoke import run_checks, write_junit_report


class SmokeHandler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="text/html", headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        cookie = self.headers.get("Cookie", "")
        authenticated = "session=ok" in cookie
        if self.path == "/auth/login":
            self._send(
                HTTPStatus.OK,
                '<form method="POST"><input type="hidden" name="csrf_token" value="token123"></form>',
            )
            return
        if self.path == "/quiz/" and authenticated:
            self._send(HTTPStatus.OK, "Logged in successfully.")
            return
        if self.path == "/dashboard/" and authenticated:
            self._send(HTTPStatus.OK, "dashboard")
            return
        if self.path == "/inspector/api/emails" and authenticated:
            self._send(HTTPStatus.OK, json.dumps([{"fileName": "sample.eml"}]), "application/json")
            return
        if self.path == "/static/images/en_garde_logo.png":
            self._send(HTTPStatus.OK, b"png", "image/png")
            return
        self._send(HTTPStatus.FORBIDDEN, "forbidden")

    def do_POST(self):  # noqa: N802
        if self.path != "/auth/login":
            self._send(HTTPStatus.NOT_FOUND, "missing")
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")
        if "username=admin" in body and "password=admin123" in body and "csrf_token=token123" in body:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/quiz/")
            self.send_header("Set-Cookie", "session=ok; Path=/")
            self.end_headers()
            return
        self._send(HTTPStatus.UNAUTHORIZED, "bad credentials")

    def log_message(self, *_args):  # noqa: D401
        return


def test_functional_smoke_checks_against_fake_server(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), SmokeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log_path = tmp_path / "smoke.log"
    junit_path = tmp_path / "smoke.xml"
    try:
        checks = run_checks(f"http://127.0.0.1:{server.server_port}", "admin", "admin123", log_path=log_path)
        write_junit_report(checks, junit_path)
    finally:
        server.shutdown()
        thread.join()

    assert all(check.passed for check in checks)
    assert log_path.exists()
    assert junit_path.exists()
