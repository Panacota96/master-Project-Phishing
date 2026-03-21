#!/usr/bin/env python3
"""
fix_eml_images.py — Replace {{.URL}} visible logo img srcs with real base64-encoded logos.

Usage:
    python scripts/fix_eml_images.py [--dry-run]

Only targets NON-linksec EML files. Linksec files already embed valid base64 PNGs.
Skips tracking pixels (1x1, display:none, style containing "none").
"""
import re
import sys
import base64
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent / "examples"

# Inline SVG data URIs for logos that can't be fetched from stable CDNs.
# Uses official brand colors so they render correctly without network access.
_SVG_NORTON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 80">'
    '<rect width="220" height="80" fill="#fff"/>'
    '<text x="12" y="54" font-family="Arial,sans-serif" font-weight="700" font-size="38" fill="#4b4b4b">Norton</text>'
    '</svg>'
)
_SVG_OKTA = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 60">'
    '<rect width="160" height="60" fill="#fff"/>'
    '<text x="8" y="42" font-family="Arial,sans-serif" font-weight="700" font-size="34" fill="#00297a">Okta</text>'
    '</svg>'
)
_SVG_DOCUSIGN = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 70">'
    '<rect width="260" height="70" fill="#fff"/>'
    '<rect x="0" y="0" width="8" height="70" fill="#FFBE25"/>'
    '<text x="20" y="46" font-family="Arial,sans-serif" font-weight="700" font-size="30" fill="#333">DocuSign</text>'
    '</svg>'
)
_SVG_GEAR = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#666">'
    '<path d="M12 15.5A3.5 3.5 0 018.5 12 3.5 3.5 0 0112 8.5a3.5 3.5 0 013.5 3.5 3.5 3.5 0 01-3.5 3.5m7.43-2.92c.04-.36.07-.73.07-1.08s-.03-.73-.07-1.08l2.32-1.81c.21-.16.27-.45.13-.68l-2.2-3.81c-.13-.23-.42-.31-.65-.23l-2.74 1.1c-.57-.44-1.18-.8-1.85-1.08L14.92 2.1c-.04-.26-.27-.45-.53-.45h-4.4c-.26 0-.49.19-.53.45L9 4.69C8.33 4.97 7.72 5.33 7.15 5.77L4.41 4.67c-.23-.09-.52 0-.65.23L1.56 8.71c-.14.23-.08.52.13.68l2.32 1.81C4.03 11.54 4 11.91 4 12.25s.03.73.07 1.08l-2.32 1.81c-.21.16-.27.45-.13.68l2.2 3.81c.13.23.42.31.65.23l2.74-1.1c.57.44 1.18.8 1.85 1.08l.41 2.59c.04.26.27.45.53.45h4.4c.26 0 .49-.19.53-.45l.41-2.59c.67-.28 1.28-.64 1.85-1.08l2.74 1.1c.23.09.52 0 .65-.23l2.2-3.81c.14-.23.08-.52-.13-.68l-2.32-1.81z"/>'
    '</svg>'
)


def _inline_svg(svg_str: str) -> str:
    """Return a data URI for an inline SVG string."""
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


# Map of img alt-text → (url_or_None, mime_type)
# None url means use the inline SVG defined above.
LOGO_MAP = {
    "Norton":    (None, "svg:norton"),
    "DHL":       ("https://upload.wikimedia.org/wikipedia/commons/a/ac/DHL_Logo.svg",
                  "image/svg+xml"),
    "Slack":     ("https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg",
                  "image/svg+xml"),
    "DocuSign":  (None, "svg:docusign"),
    "Signature": (None, "svg:docusign"),
    "Okta":      (None, "svg:okta"),
    "Apple":     ("https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg",
                  "image/svg+xml"),
    "Google":    ("https://www.gstatic.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png",
                  "image/png"),
    "Settings":  (None, "svg:gear"),
}

_INLINE_SVGS = {
    "svg:norton":   _inline_svg(_SVG_NORTON),
    "svg:okta":     _inline_svg(_SVG_OKTA),
    "svg:docusign": _inline_svg(_SVG_DOCUSIGN),
    "svg:gear":     _inline_svg(_SVG_GEAR),
}

# Directories to fix (linksec already has valid base64, spam images not critical)
TARGET_DIRS = [
    "impersonation",
    "impersonation-urgency",
    "fake-invoice",
    "legit-impersonation",
    "punycode",
    "realistic_templates",
]

_logo_cache: dict = {}


def fetch_logo(url: str, mime: str) -> str:
    """Return a data URI for the logo. Handles inline SVGs and remote URLs."""
    if mime.startswith("svg:"):
        return _INLINE_SVGS.get(mime, "")
    if url in _logo_cache:
        return _logo_cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        b64 = base64.b64encode(data).decode()
        result = f"data:{mime};base64,{b64}"
        _logo_cache[url] = result
        return result
    except Exception as exc:
        print(f"  WARNING: could not fetch {url}: {exc}")
        return ""


def is_tracking_pixel(img_tag: str) -> bool:
    """Return True if the img tag is a hidden tracking pixel."""
    if re.search(r'width=["\']?1["\']', img_tag, re.IGNORECASE):
        return True
    if re.search(r'height=["\']?1["\']', img_tag, re.IGNORECASE):
        return True
    if re.search(r'display\s*:\s*none', img_tag, re.IGNORECASE):
        return True
    return False


def get_alt(img_tag: str) -> str:
    m = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def fix_file(eml_path: Path, dry_run: bool = False) -> int:
    """Fix all visible {{.URL}} logo images in an EML file. Returns number of replacements."""
    content = eml_path.read_text(encoding="utf-8", errors="replace")
    replacements = 0

    def replace_img(m):
        nonlocal replacements
        img_tag = m.group(0)
        if is_tracking_pixel(img_tag):
            return img_tag
        if not re.search(r'src=["\']?\{\{\.(?:URL|TrackingURL)\}\}', img_tag, re.IGNORECASE):
            return img_tag
        alt = get_alt(img_tag)
        entry = LOGO_MAP.get(alt)
        if not entry:
            print(f"  SKIP unknown alt='{alt}' in {eml_path.name}")
            return img_tag
        url, mime = entry
        print(f"  -> {alt}: fetching logo...")
        data_uri = fetch_logo(url, mime)
        if not data_uri:
            return img_tag
        new_tag = re.sub(
            r'src=["\']?\{\{\.(?:URL|TrackingURL)\}\}["\']?',
            f'src="{data_uri}"',
            img_tag,
            flags=re.IGNORECASE,
        )
        replacements += 1
        return new_tag

    new_content = re.sub(r'<img[^>]+>', replace_img, content, flags=re.IGNORECASE | re.DOTALL)
    if replacements and not dry_run:
        eml_path.write_text(new_content, encoding="utf-8")
    return replacements


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    total = 0
    for dirname in TARGET_DIRS:
        dirpath = ROOT / dirname
        if not dirpath.is_dir():
            continue
        for eml_file in sorted(dirpath.glob("*.eml")):
            n = fix_file(eml_file, dry_run=dry_run)
            if n:
                print(f"  Fixed {n} image(s) in {dirname}/{eml_file.name}")
                total += n

    print(f"\nDone. Total images fixed: {total}")


if __name__ == "__main__":
    main()
