# Download EML Examples from TryHackMe

## Prerequisites
- TryHackMe VM must be **running** and accessible
- Update the IP/URL below if your VM address changes

> **Security note:** Never commit real browser session cookies to version control.
> Replace the placeholder values below with cookies captured live from your own
> browser session (DevTools → Network → Copy as PowerShell) and run the script
> locally. Discard the cookies after use.

---

## Cookie placeholders

Before running any script below, replace these variables with the values from
your own browser session:

```powershell
$VM_IP     = "10-64-147-3"   # Replace with your TryHackMe VM IP segment
$USER_ID   = "<YOUR_THM_USER_ID>"
$DEVICE_ID = "<YOUR_INTERCOM_DEVICE_ID>"
$SESSION   = "<YOUR_INTERCOM_SESSION_TOKEN>"
$OUT_DIR   = "$HOME\examples"   # Adjust to your local clone path
```

---

## Helper function (paste once per session)

```powershell
function Get-ThmEml {
    param([string]$EmlFile, [string]$OutSubdir)
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    $session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id",         $USER_ID,   "/", ".tryhackme.com")))
    $session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint",      $USER_ID,   "/", ".tryhackme.com")))
    $session.Cookies.Add((New-Object System.Net.Cookie("_cioid",              $USER_ID,   "/", ".tryhackme.com")))
    $session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", $DEVICE_ID, "/", ".tryhackme.com")))
    $session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6",   $SESSION,   "/", ".tryhackme.com")))
    $baseUrl = "https://$VM_IP.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com"
    Invoke-WebRequest -UseBasicParsing `
        -Uri "$baseUrl/api/emails/$EmlFile" `
        -WebSession $session `
        -Headers @{"Accept"="*/*"; "Referer"="$baseUrl/"} `
        -OutFile "$OUT_DIR\$OutSubdir\$EmlFile"
}
```

---

## 1. Fake Invoice Example

```powershell
Get-ThmEml "fakeinvoice-urgency-spoofing-socialeng.eml" "fake-invoice"
```

---

## 2. Impersonation Example

```powershell
Get-ThmEml "impersonation-attachment-socialeng-spoof.eml" "impersonation"
```

---

## 3. Spam / Marketing Example

```powershell
Get-ThmEml "marketing-spam-logistics.eml" "spam"
```

---

## 4. Legit App Impersonation Example

```powershell
Get-ThmEml "legitapp-impersonation-externaldomain-socialeng.eml" "legit-impersonation"
```

---

## 5. Punycode Impersonation Example

```powershell
Get-ThmEml "punycode-impersonation-legitapp-socialeng.eml" "punycode"
```

---

## 6. Impersonation + Social Engineering + Urgency Example

```powershell
Get-ThmEml "impersonation-socialeng-urgency.eml" "impersonation-urgency"
```

---

## Notes
- If cookies expire, re-capture the request from your browser (DevTools > Network > Copy as PowerShell) and update the variables at the top of this file.
- If the VM IP changes, update `$VM_IP` above.
- Output directories (relative to your local clone):
  - `examples/fake-invoice/`
  - `examples/impersonation/`
  - `examples/spam/`
  - `examples/legit-impersonation/`
  - `examples/punycode/`
  - `examples/impersonation-urgency/`
