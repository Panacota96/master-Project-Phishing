# Adding New EML Files to the Inspector

This guide covers the end-to-end process for adding a new email sample to the Email Threat Inspector.

---

## Step 1: Create the EML File

Place your `.eml` file in the `examples/` directory. All EML files must use `multipart/alternative` structure for consistent parsing by the inspector's `email` stdlib parser.

Minimum required structure:

```
Content-Type: multipart/alternative; boundary="boundary_string"

--boundary_string
Content-Type: text/plain; charset="utf-8"

Plain text version of the email body.

--boundary_string
Content-Type: text/html; charset="utf-8"

<html><body>HTML version of the email body.</body></html>

--boundary_string--
```

See the [Improving Example Emails section in README.md](../../README.md#improving-example-emails-realism-checklist) for a full realism checklist (multipart, inline images, tracking pixels, header spoofing, etc.).

---

## Step 2: Add an Entry to `answer_key.py`

Open `app/inspector/answer_key.py` and add an entry to the `ANSWER_KEY` dict:

```python
"your-filename.eml": {
    "classification": "Phishing",   # or "Spam"
    "signals": ["impersonation", "urgency", "fakelogin"],
    "explanation": "This email impersonates a known brand to steal credentials."
},
```

**Valid signal names** (lowercase, alphanumeric only):

| Signal | Display name |
|---|---|
| `impersonation` | Impersonation |
| `punycode` | Typosquatting / Punycode |
| `externaldomain` | External Sender Domain |
| `spoof` | Spoofing |
| `socialeng` | Social Engineering |
| `urgency` | Urgency |
| `fakeinvoice` | Fake Invoice |
| `attachment` | Malicious Attachment |
| `fakelogin` | Fake Login Page |
| `sidechannel` | Side Channel Communication |

> For **Spam** emails, set `"signals": []` — students are not required to select any signals.

The required signal count is derived from `len(signals)` — do not hardcode 3.

---

## Step 3: Upload to S3

```bash
# Upload to dev
aws s3 cp examples/your-filename.eml \
  s3://phishing-app-dev-eu-west-3/eml-samples/your-filename.eml

# Upload to prod
aws s3 cp examples/your-filename.eml \
  s3://phishing-app-prod-eu-west-3/eml-samples/your-filename.eml
```

Or sync the entire examples directory:

```bash
aws s3 sync examples/ s3://phishing-app-dev-eu-west-3/eml-samples/ \
  --exclude "*" --include "*.eml"
```

---

## Step 4: Validate Realism

Run the built-in validator to ensure the new file meets baseline realism criteria:

```bash
make validate-eml
```

Reports are written to `examples/realism_report.json`. If a check should be skipped for a specific file (e.g., a deliberately simple spam sample), add it to `examples/realism_allowlist.json`.

---

## Step 5: Verify in the Inspector

1. Restart the Flask app (or wait for Lambda to pick up the new S3 file).
2. Log in as an admin and open the Inspector.
3. Confirm the new email appears in your session pool (pool is sampled per-session, so you may need to clear your session or start a fresh browser session).
4. Check **Admin → Inspector Analytics → View Answer Key** to confirm the entry is listed with the correct classification and signal count.
