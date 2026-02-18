"""Tests for the EML realism validator."""

from email.message import EmailMessage
from pathlib import Path

from scripts.validate_eml_realism import validate_eml


def _write_eml(path: Path, *, include_link: bool = True, include_image: bool = True):
    msg = EmailMessage()
    msg["From"] = "Test <test@example.com>"
    msg["To"] = "User <user@example.com>"
    msg["Subject"] = "Test"

    text_body = "Hello\n"
    html_body = "<html><body>"
    if include_link:
        html_body += '<a href="https://example.com">Link</a>'
    if include_image:
        html_body += '<img src="cid:logo" />'
    html_body += "</body></html>"

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    path.write_text(msg.as_string())


def test_validator_passes_minimum(tmp_path):
    eml = tmp_path / "ok.eml"
    _write_eml(eml, include_link=True, include_image=True)
    errors, warnings = validate_eml(eml, {'defaults': {'skip_image': False}})
    assert errors == []
    assert warnings == []


def test_validator_fails_without_link_or_attachment(tmp_path):
    eml = tmp_path / "nolink.eml"
    _write_eml(eml, include_link=False, include_image=True)
    errors, warnings = validate_eml(eml, {'defaults': {'skip_image': False}})
    assert 'missing links and attachments' in errors
    assert warnings == []
