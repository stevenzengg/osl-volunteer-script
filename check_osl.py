import requests
import hashlib
import smtplib
from email.message import EmailMessage
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import sys

load_dotenv()

OSL_USERNAME = os.environ["OSL_USERNAME"]
OSL_PASSWORD = os.environ["OSL_PASSWORD"]
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

EVENT_URL = "https://ape.festivol.net/goEvents.action?eventsID=854"
LOGIN_URL = "https://ape.festivol.net/loginLandingPage.action"
BASELINE_HASH = "c6a49edc308c66027ed4b19a113bfcc32190bbb3688aa53f2ce49b6cc8698e63"


def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("No email credentials set, skipping notification")
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Email notification sent")


session = requests.Session()

login_resp = session.post(LOGIN_URL, data={
    "username": OSL_USERNAME,
    "password": OSL_PASSWORD,
}, allow_redirects=True)

try:
    login_data = login_resp.json()
    if login_data.get("volunteers", {}).get("email") == OSL_USERNAME:
        print("Logged in successfully")
    else:
        print("LOGIN FAILED - unexpected response")
        print(f"Response: {login_resp.text[:500]}")
        sys.exit(1)
except Exception:
    print("LOGIN FAILED - check credentials or field names")
    print(f"Status: {login_resp.status_code}")
    print(f"Response: {login_resp.text[:500]}")
    sys.exit(1)

r = session.get(EVENT_URL)
soup = BeautifulSoup(r.text, "html.parser")

# Check 1: Apply button href/onclick
apply_span = soup.find("span", string=lambda t: t and "Apply" in t)
button_changed = False

if apply_span:
    apply_link = apply_span.find_parent("a")
    if apply_link:
        href = apply_link.get("href", "")
        onclick = apply_link.get("onclick", "")
        print(f"Apply button href: {href}")
        print(f"Apply button onclick: {onclick}")
        button_changed = "void(0)" not in href or "notopenMsg" not in onclick
    else:
        print("Apply link wrapper not found — page structure changed")
        button_changed = True
else:
    print("Apply span not found — page structure changed")
    button_changed = True

# Check 2: Hash of the buttons section
buttons_html = ""
for span in soup.find_all("span", class_="evt-btn"):
    a = span.find_parent("a")
    if a:
        buttons_html += str(a)

current_hash = hashlib.sha256(buttons_html.encode()).hexdigest()
hash_changed = current_hash != BASELINE_HASH
print(f"Buttons hash: {current_hash}")
print(f"Hash changed: {hash_changed}")

# Alert if either check triggers
if button_changed or hash_changed:
    print("SOMETHING CHANGED — APPS MAY BE OPEN!")
    body = ""
    if button_changed:
        body += "Apply button is no longer inactive!\n"
    if hash_changed:
        body += "Page content has changed from baseline!\n"
    body += f"\nGO CHECK NOW: {EVENT_URL}"
    send_email("OSL VOLUNTEER APPS — SOMETHING CHANGED!", body)
else:
    print("Not yet... no changes detected")
