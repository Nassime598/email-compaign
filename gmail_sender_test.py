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

def send_test_email(service, raw_headers: str, body_html: str, boundary: str = "boundary123"):
    """
    - `raw_headers`: Full header block as string (already includes From, To, Subject, etc).
    - `body_html`: Body of the email.
    - `boundary`: MIME boundary.
    """

    # MIME body
    mime_body = (
        f"--{boundary}\n"
        "Content-Type: text/html; charset=utf-8\n"
        "Content-Transfer-Encoding: quoted-printable\n"
        "\n"
        f"{body_html}\n"
        f"--{boundary}--"
    )

    # Full raw message
    full_message = raw_headers.strip() + "\n\n" + mime_body

    # Base64 encode
    encoded_message = base64.urlsafe_b64encode(full_message.encode('utf-8')).decode('utf-8')

    # Send
    return service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
