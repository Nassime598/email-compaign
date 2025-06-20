import time
import re
import random
import string
import json
from concurrent.futures import ThreadPoolExecutor
import googleapiclient.errors
from database import db
from models import Campaign, CampaignRecipient, CampaignUser, ServiceAccount, User, CampaignLog
from gmail_sender import create_gmail_service, send_email

DAILY_GMAIL_QUOTA_LIMIT = 2000
QUOTA_SAFETY_MARGIN = 1950
MAX_WORKERS = 200

def replace_tags(text, recipient_email):
    if not text:
        return ''
    text = text.replace('[email]', recipient_email)
    text = text.replace('[mail_date]', time.strftime('%a, %d %b %Y %H:%M:%S +0000'))

    def random_replacer(match):
        length = int(match.group(1))
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return re.sub(r'\[RANDOM:(\d+)\]', random_replacer, text)

class EmailWorker:
    def __init__(self, redis_conn, campaign_id, log_file):
        self.redis_conn = redis_conn
        self.campaign_id = campaign_id
        self.running = False
        self.log_file = log_file
        self.service_cache = {}
        self.user_send_count = {}
        self.success_count = 0
        self.failure_count = 0
        self.send_speed = None
        self.executor = None

    def load_recipients(self):
        queue_key = f"campaign:{self.campaign_id}:recipients"
        if self.redis_conn.llen(queue_key) == 0:
            campaign_recipients = CampaignRecipient.query.filter_by(campaign_id=self.campaign_id).all()
            for r in campaign_recipients:
                self.redis_conn.rpush(queue_key, r.email)

    def get_next_recipient(self):
        queue_key = f"campaign:{self.campaign_id}:recipients"
        email = self.redis_conn.lpop(queue_key)
        if email:
            return email.decode('utf-8')
        return None

    def get_cached_service(self, sender_email, service_account_path):
        if sender_email not in self.service_cache:
            service = create_gmail_service(sender_email, service_account_path)
            self.service_cache[sender_email] = service
        return self.service_cache[sender_email]

    def send_email_with_retry(self, service, full_raw_message):
        max_retries = 5
        backoff = 1
        for attempt in range(max_retries):
            try:
                return send_email(service, full_raw_message)
            except googleapiclient.errors.HttpError as e:
                if e.resp.status in [429, 500, 502, 503, 504]:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                else:
                    raise
        raise Exception(f"Failed after {max_retries} retries")

    def send_single_email(self, sender_email, service_account_path, recipient_email, campaign, headers):
        if not self.running:
            return

        self.user_send_count.setdefault(sender_email, 0)
        if self.user_send_count[sender_email] >= QUOTA_SAFETY_MARGIN:
            return

        service = self.get_cached_service(sender_email, service_account_path)

        dynamic_headers = []
        for header in headers:
            value = header['value'].replace('[user-sender]', sender_email)
            value = replace_tags(value, recipient_email)
            dynamic_headers.append(f"{header['name']}: {value}")

        raw_headers_str = "\n".join(dynamic_headers)
        full_body = replace_tags(campaign.body_html, recipient_email)
        full_raw_message = raw_headers_str.strip() + "\n\n" + full_body

        try:
            response = self.send_email_with_retry(service, full_raw_message)
            self.log_email(sender_email, recipient_email, "SUCCESS", response.get('id'))
            self.user_send_count[sender_email] += 1
            self.success_count += 1
        except Exception as e:
            self.log_email(sender_email, recipient_email, "FAILED", error=str(e))
            self.failure_count += 1

    def is_paused(self):
        return self.redis_conn.get(f"campaign:{self.campaign_id}:paused") == b"1"

    def adaptive_sleep(self):
        base_sleep = 1.0 / self.send_speed
        if self.failure_count + self.success_count == 0:
            return base_sleep
        error_rate = self.failure_count / (self.failure_count + self.success_count)
        if error_rate > 0.1:
            return base_sleep * 2
        return base_sleep

    def run(self):
        from app import app

        with app.app_context():
            self.running = True
            self.load_recipients()

            campaign = Campaign.query.get(self.campaign_id)
            self.send_speed = campaign.send_speed
            headers = json.loads(campaign.headers_json or '[]')
            campaign_users = CampaignUser.query.filter_by(campaign_id=self.campaign_id).all()

            senders = [(u.email, ServiceAccount.query.get(u.service_account_id).filename) for u in campaign_users]
            sender_cycle = iter(senders)

            self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

            while True:
                if not self.running:
                    break
                if self.is_paused():
                    time.sleep(5)
                    continue

                recipient_email = self.get_next_recipient()
                if not recipient_email:
                    break

                try:
                    sender_email, service_account_path = next(sender_cycle)
                except StopIteration:
                    sender_cycle = iter(senders)
                    sender_email, service_account_path = next(sender_cycle)

                self.executor.submit(
                    self.send_single_email,
                    sender_email,
                    service_account_path,
                    recipient_email,
                    campaign,
                    headers
                )

                time.sleep(self.adaptive_sleep())

            self.executor.shutdown(wait=True)

    def stop(self):
        self.running = False

    def log_email(self, sender_email, recipient_email, status, message_id=None, error=None):
        log = CampaignLog(
            campaign_id=self.campaign_id,
            recipient_email=recipient_email,
            status=status,
            error=error,
            message_id=message_id
        )
        db.session.add(log)
        db.session.commit()

        with open(self.log_file, 'a') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if status == "SUCCESS":
                f.write(f"[{timestamp}] From {sender_email} -> {recipient_email}: SUCCESS ({message_id})\n")
            else:
                f.write(f"[{timestamp}] From {sender_email} -> {recipient_email}: FAILED - {error}\n")
