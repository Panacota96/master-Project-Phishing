#!/usr/bin/env python3
"""
fix_eml_names.py — Replace {{.FirstName}} / {{.LastName}} with realistic values.

Rules:
  - Targeted / spear-phishing emails  → real European name (realistic for ESME students)
  - Mass / bulk phishing emails        → generic greeting ("Customer", "Valued Member")
  - To: header placeholder            → realistic display name

Usage:
    python scripts/fix_eml_names.py [--dry-run]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "examples"

# (first, last) pairs for targeted emails  –  realistic French/European names
TARGETED = {
    # fake-invoice
    "refund-scam.eml":              ("Sophie",  "Martin"),
    "phishing-attachment-1.eml":    ("Thomas",  "Dupont"),
    "phishing-attachment-2.eml":    ("Marc",    "Lebrun"),
    # impersonation
    "lateral-phish.eml":            ("Léa",     "Bernard"),
    "pixel-tracking.eml":           ("Nicolas", "Moreau"),
    "protected-archive.eml":        ("Sophie",  "Martin"),
    "thread-hijacking.eml":         ("Thomas",  "Dupont"),
    "missed-deadline.eml":          ("Camille", "Leroy"),
    # legit-impersonation
    "legit-app-3.eml":              ("Marc",    "Lebrun"),
    "legit-app-4.eml":              ("Léa",     "Bernard"),
    # realistic templates
    "realistic-invoice-qr.eml":     ("Thomas",  "Dupont"),
    "realistic-it-reset.eml":       ("Sophie",  "Martin"),
    "realistic-shipping-qr.eml":    ("Marc",    "Lebrun"),
}

# For everything else use "Customer" / "" so greetings read:
# "Dear Customer," "Hello Customer," "Hi Customer," "Congratulations, Customer!"
GENERIC_FIRST = "Customer"
GENERIC_LAST  = ""


def replace_names(content: str, first: str, last: str) -> str:
    """Replace all GoPhish-style name placeholders in content."""
    content = re.sub(r"\{\{\.FirstName\}\}", first, content)
    content = re.sub(r"\{\{\.LastName\}\}",  last,  content)
    # Also handle space before empty last name: "Dear Customer ," → "Dear Customer,"
    if not last:
        content = re.sub(r"(Customer)\s+,", r"\1,", content)
        content = re.sub(r"(Customer)\s+Member", r"\1", content)
    return content


def fix_file(eml_path: Path, dry_run: bool = False) -> int:
    name = eml_path.name
    if name in TARGETED:
        first, last = TARGETED[name]
    else:
        first, last = GENERIC_FIRST, GENERIC_LAST

    content = eml_path.read_text(encoding="utf-8", errors="replace")
    if "{{.FirstName}}" not in content and "{{.LastName}}" not in content:
        return 0

    original = content
    content = replace_names(content, first, last)

    # Also fix To: header if it still shows a raw placeholder as display name
    # e.g.  To: "Valued" <user@example.com>  →  leave as-is (already handled above)

    if content == original:
        return 0
    if not dry_run:
        eml_path.write_text(content, encoding="utf-8")
    return 1


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    total = 0
    for eml_path in sorted(ROOT.rglob("*.eml")):
        n = fix_file(eml_path, dry_run=dry_run)
        if n:
            rel = eml_path.relative_to(ROOT)
            first = TARGETED.get(eml_path.name, (GENERIC_FIRST,))[0]
            label = first if eml_path.name in TARGETED else "generic"
            print(f"  Fixed [{label:>8}]  {rel}")
            total += n

    print(f"\nDone. {total} file(s) updated.")


if __name__ == "__main__":
    main()
