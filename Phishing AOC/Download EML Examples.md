# Download EML Examples from TryHackMe

## Prerequisites
- TryHackMe VM must be **running** and accessible
- Update the IP/URL below if your VM address changes

---

## 1. Fake Invoice Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/fakeinvoice-urgency-spoofing-socialeng.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\fake-invoice\fakeinvoice-urgency-spoofing-socialeng.eml"
```

---

## 2. Impersonation Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/impersonation-attachment-socialeng-spoof.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\impersonation\impersonation-attachment-socialeng-spoof.eml"
```

---

## 3. Spam / Marketing Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/marketing-spam-logistics.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\spam\marketing-spam-logistics.eml"
```

---

## 4. Legit App Impersonation Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/legitapp-impersonation-externaldomain-socialeng.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\legit-impersonation\legitapp-impersonation-externaldomain-socialeng.eml"
```

---

## 5. Punycode Impersonation Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/punycode-impersonation-legitapp-socialeng.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\punycode\punycode-impersonation-legitapp-socialeng.eml"
```

---

## 6. Impersonation + Social Engineering + Urgency Example

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0"
$session.Cookies.Add((New-Object System.Net.Cookie("_ga", "GA1.1.22156733.1769454898", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_anonymous_id", "15f364db-a8d9-4c9f-87b3-c4095f056014", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ajs_user_id", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-device-id-pgpbhph6", "aeddfdf4-dbc5-456e-9893-6b564c94b9a6", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_gcl_au", "1.1.1644970611.1769454898.1892155888.1769454909.1769454911", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_cioid", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id", "1770846394420", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("logged-in-hint", "67f0f84312915140405a9277", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("intercom-session-pgpbhph6", "M0hwemM3Tk5kekxoNlNFZjN5bytsWEZUbEZZbEdaN1ZsNjN6Z0VVd2c1MXdvTndoRWw5UWNROU5yN1dvNXZQd0ZjNjRXTllpQjltTUtZNVhMZ1dtYlEzQk5mVVBmR0FkTmo0N0JienZ0MjA9LS1yb0huREx5Ui9NQnJ2S1NuME14eVdRPT0=--5923cba7ed71cb6270adddfe863d7aca0060059a", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("analytics_session_id.last_access", "1770846514040", "/", ".tryhackme.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("_ga_Z8D4WL3D4P", "GS2.1.s1770846497`$o7`$g1`$t1770846591`$j60`$l0`$h0", "/", ".tryhackme.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/api/emails/impersonation-socialeng-urgency.eml" -WebSession $session -Headers @{"Accept"="*/*"; "Accept-Language"="en-US,en;q=0.9"; "Referer"="https://10-64-147-3.reverse-proxy.cell-prod-us-east-1a.vm.tryhackme.com/"} -OutFile "$HOME\OneDrive - ESME\Documents\INGE3C\Project INGE3C\master-Project-Phishing\examples\impersonation-urgency\impersonation-socialeng-urgency.eml"
```

---

## Notes
- If cookies expire, re-capture the request from your browser (DevTools > Network > Copy as PowerShell)
- If the VM IP changes, replace `10-64-147-3` in all URLs
- Files are saved to:
  - `examples/fake-invoice/`
  - `examples/impersonation/`
  - `examples/spam/`
  - `examples/legit-impersonation/`
  - `examples/punycode/`
  - `examples/impersonation-urgency/`
