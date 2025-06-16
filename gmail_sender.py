import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

def create_gmail_service(user_email, service_account_path):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://mail.google.com/'],
        subject=user_email
    )
    return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

def send_email(service, raw_headers, body_html, boundary="boundary123"):
    full_email = raw_headers.strip() + "\n\n"

    mime_body = (
        f"--{boundary}\n"
        "Content-Type: text/html; charset=utf-8\n"
        "Content-Transfer-Encoding: quoted-printable\n"
        "\n"
        f"{body_html}\n"
        f"--{boundary}--"
    )

    full_message = full_email + mime_body
    encoded_message = base64.urlsafe_b64encode(full_message.encode('utf-8')).decode('utf-8')
    return service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
