from database import db
from datetime import datetime

class ServiceAccount(db.Model):
    __tablename__ = 'service_accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    filename = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False)
    service_account_id = db.Column(db.Integer, db.ForeignKey('service_accounts.id'), nullable=False)

class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    subject = db.Column(db.String(512), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    send_type = db.Column(db.String(10), nullable=False)
    x_delay = db.Column(db.String(50))
    send_speed = db.Column(db.Integer, default=1)
    emails_per_user = db.Column(db.Integer, default=10)
    test_email = db.Column(db.String(256))
    test_every = db.Column(db.Integer, default=10)
    headers_json = db.Column(db.Text)  # <-- NEW FIELD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CampaignRecipient(db.Model):
    __tablename__ = 'campaign_recipients'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)

class CampaignUser(db.Model):
    __tablename__ = 'campaign_users'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class CampaignLog(db.Model):
    __tablename__ = 'campaign_logs'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    recipient_email = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # SUCCESS / FAILED
    error = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
