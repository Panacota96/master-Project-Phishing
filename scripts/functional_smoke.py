from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin

import requests


DEFAULT_ADMIN_USERNAME = os.environ.get("SMOKE_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("SMOKE_ADMIN_PASSWORD", "admin123")


@dataclass
class SmokeCheck:
    name: str
    passed: bool
    detail: str = ""


class SmokeRunner:
    def __init__(self, base_url: str, session: requests.Session, log_path: Path) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session
        self.log_path = log_path
        self.log_lines: list[str] = []

    def log(self, message: str) -> None:
        line = f"[functional-smoke] {message}"
        self.log_lines.append(line)
        print(line)

    def absolute_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self.absolute_url(path)
        response = self.session.request(method, url, timeout=15, **kwargs)
        self.log(f"{method} {url} -> {response.status_code}")
        return response

    def wait_for_login(self, timeout_seconds: int = 180) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                response = self.request("GET", "/auth/login")
                if response.status_code == 200:
                    return
            except requests.RequestException as exc:
                self.log(f"waiting for login page: {exc}")
            time.sleep(5)
        raise RuntimeError(f"Timed out waiting for {self.absolute_url('/auth/login')}")

    def persist_log(self) -> None:
        self.log_path.write_text("\n".join(self.log_lines) + "\n", encoding="utf-8")


def fetch_csrf_token(runner: SmokeRunner) -> str:
    response = runner.request("GET", "/auth/login")
    response.raise_for_status()
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text, re.DOTALL)
    if not match:
        raise RuntimeError("Unable to locate csrf_token on /auth/login.")
    return html.unescape(match.group(1))


def run_checks(base_url: str, admin_username: str, admin_password: str, *, log_path: Path) -> list[SmokeCheck]:
    session = requests.Session()
    runner = SmokeRunner(base_url, session, log_path)
    checks: list[SmokeCheck] = []
    try:
        runner.wait_for_login()
        checks.append(run_check("login page", lambda: assert_status(runner.request("GET", "/auth/login"), 200)))
        csrf_token = fetch_csrf_token(runner)
        login_response = runner.request(
            "POST",
            "/auth/login",
            data={
                "username": admin_username,
                "password": admin_password,
                "csrf_token": csrf_token,
                "submit": "Login",
            },
            allow_redirects=True,
        )
        checks.append(
            assert_response_contains(
                login_response,
                200,
                "/quiz/",
                "quiz list after login",
                "Logged in successfully.",
            )
        )
        checks.append(run_check("quiz list", lambda: assert_status(runner.request("GET", "/quiz/"), 200)))
        checks.append(run_check("dashboard page", lambda: assert_status(runner.request("GET", "/dashboard/"), 200)))
        checks.append(
            run_check(
                "inspector email api",
                lambda: assert_json_array(runner.request("GET", "/inspector/api/emails")),
            )
        )
        checks.append(
            run_check(
                "static asset",
                lambda: assert_status(runner.request("GET", "/static/images/en_garde_logo.png"), 200),
            )
        )
    finally:
        runner.persist_log()
    return checks


def run_check(name: str, assertion: Callable[[], str]) -> SmokeCheck:
    try:
        detail = assertion()
        return SmokeCheck(name=name, passed=True, detail=detail)
    except Exception as exc:  # noqa: BLE001
        return SmokeCheck(name=name, passed=False, detail=str(exc))


def assert_status(response: requests.Response, expected_status: int) -> str:
    if response.status_code != expected_status:
        raise AssertionError(f"expected HTTP {expected_status}, got {response.status_code}")
    return f"HTTP {expected_status}"


def assert_response_contains(
    response: requests.Response,
    expected_status: int,
    expected_path_fragment: str,
    name: str,
    expected_text: str,
) -> SmokeCheck:
    if response.status_code != expected_status:
        return SmokeCheck(
            name=name,
            passed=False,
            detail=f"expected HTTP {expected_status}, got {response.status_code}",
        )
    final_path = response.url
    if expected_path_fragment not in final_path:
        return SmokeCheck(
            name=name,
            passed=False,
            detail=f"expected redirect to contain '{expected_path_fragment}', got '{final_path}'",
        )
    if expected_text not in response.text:
        return SmokeCheck(
            name=name,
            passed=False,
            detail=f"expected response body to contain '{expected_text}'",
        )
    return SmokeCheck(name=name, passed=True, detail=f"redirected to {final_path}")


def assert_json_array(response: requests.Response) -> str:
    if response.status_code != 200:
        raise AssertionError(f"expected HTTP 200, got {response.status_code}")
    payload = response.json()
    if not isinstance(payload, list):
        raise AssertionError("expected JSON array response")
    return f"{len(payload)} emails available"


def write_junit_report(checks: list[SmokeCheck], output_path: Path) -> None:
    suite = ET.Element("testsuite", name="functional-smoke", tests=str(len(checks)))
    failures = 0
    for check in checks:
        case = ET.SubElement(suite, "testcase", name=check.name)
        if check.passed:
            ET.SubElement(case, "system-out").text = check.detail
            continue
        failures += 1
        failure = ET.SubElement(case, "failure", message=check.detail)
        failure.text = check.detail
    suite.set("failures", str(failures))
    tree = ET.ElementTree(suite)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HTTP smoke checks against the local or deployed application.")
    parser.add_argument("--mode", choices=("local", "remote"), required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--admin-username", default=DEFAULT_ADMIN_USERNAME)
    parser.add_argument("--admin-password", default=DEFAULT_ADMIN_PASSWORD)
    parser.add_argument("--junit-xml", default="functional-smoke-report.xml")
    parser.add_argument("--log-file", default="functional-smoke.log")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = run_checks(
        args.base_url,
        args.admin_username,
        args.admin_password,
        log_path=Path(args.log_file),
    )
    write_junit_report(checks, Path(args.junit_xml))
    failed = [check for check in checks if not check.passed]
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"{status}: {check.name} - {check.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
