import base64
import re
import time
import random
import string
from google.oauth2 import service_account
from googleapiclient.discovery import build

def create_gmail_service(user_email, service_account_path):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://mail.google.com/'],
        subject=user_email
    )
    return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

def replace_tags(text, recipient_email, sender_email):
    if not text:
        return ''
    text = text.replace('[email]', recipient_email)
    text = text.replace('[user-sender]', sender_email)
    text = text.replace('[mail_date]', time.strftime('%a, %d %b %Y %H:%M:%S +0000'))

    def random_replacer(match):
        length = int(match.group(1))
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return re.sub(r'\[RANDOM:(\d+)\]', random_replacer, text)

def send_test_email(service, raw_headers: str, body_html: str, boundary: str = "boundary123"):
    # Extract recipient from To header for tag replacement
    recipient_email = ""
    for line in raw_headers.splitlines():
        if line.lower().startswith("to:"):
            recipient_email = line.split(":", 1)[1].strip()
            break

    # Extract sender from From header for tag replacement
    sender_email = ""
    for line in raw_headers.splitlines():
        if line.lower().startswith("from:"):
            match = re.search(r'<([^>]+)>', line)
            sender_email = match.group(1).strip() if match else line.split(":", 1)[1].strip()
            break

    # Replace tags in headers and body
    raw_headers = replace_tags(raw_headers, recipient_email, sender_email)
    body_html = replace_tags(body_html, recipient_email, sender_email)

    # MIME body
    mime_body = (
        f"--{boundary}\n"
        "Content-Type: text/html; charset=utf-8\n"
        "Content-Transfer-Encoding: quoted-printable\n"
        "\n"
        f"{body_html}\n"
        f"--{boundary}--"
    )

    # Full message
    full_message = raw_headers.strip() + "\n\n" + mime_body
    encoded_message = base64.urlsafe_b64encode(full_message.encode('utf-8')).decode('utf-8')

    # Send
    return service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
