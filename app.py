import base64
import os
import json
import threading
import redis
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from config import Config
from database import db, migrate
from models import ServiceAccount, User, Campaign, CampaignRecipient, CampaignUser, CampaignLog
from worker import EmailWorker
from admin import setup_admin
from gmail_sender import create_gmail_service, send_email
from gmail_sender_test import send_test_email
from worker import replace_tags  # Ensure this import exists at top

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)
setup_admin(app, db)

socketio = SocketIO(app, cors_allowed_origins="*")
r = redis.from_url(app.config['REDIS_URL'])

worker = None
worker_thread = None
log_file = 'logs/campaign.log'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/campaigns')
def campaigns_page():
    return render_template('campaigns.html')

@app.route('/test_send')
def test_send_page():
    return render_template('test_send.html')

@app.route('/service_accounts')
def service_accounts_page():
    return render_template('service_accounts.html')

@app.route('/start_campaign/<int:campaign_id>', methods=['POST'])
def start_campaign(campaign_id):
    global worker, worker_thread
    if worker is None or not worker.running:
        worker = EmailWorker(r, campaign_id, log_file)
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.start()
        return jsonify({"status": "Campaign Started"})
    else:
        return jsonify({"status": "Already Running"})

@app.route('/pause_campaign', methods=['POST'])
def pause_campaign():
    data = request.get_json()
    campaign_id = data.get('campaign_id')
    if not campaign_id:
        return jsonify({"error": "Missing campaign_id"}), 400

    r.set(f"campaign:{campaign_id}:paused", "1")
    return jsonify({"status": f"Campaign {campaign_id} Paused"})

@app.route('/resume_campaign', methods=['POST'])
def resume_campaign():
    data = request.get_json()
    campaign_id = data.get('campaign_id')
    if not campaign_id:
        return jsonify({"error": "Missing campaign_id"}), 400

    r.delete(f"campaign:{campaign_id}:paused")
    return jsonify({"status": f"Campaign {campaign_id} Resumed"})

@app.route('/logs', methods=['GET'])
def get_logs():
    if not os.path.exists(log_file):
        return jsonify({"logs": []})
    with open(log_file, 'r') as f:
        lines = f.readlines()
    return jsonify({"logs": lines[-100:]})

@app.route('/dashboard_data')
def dashboard_data():
    success_count = CampaignLog.query.filter_by(status='SUCCESS').count()
    failed_count = CampaignLog.query.filter_by(status='FAILED').count()
    return jsonify({"success": success_count, "failed": failed_count})

@app.route('/upload_service_account', methods=['POST'])
def upload_service_account():
    name = request.form.get('name')
    file = request.files.get('file')
    if not name or not file:
        return jsonify({'error': 'Missing name or file'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join('uploads', 'service_accounts', filename)
    file.save(save_path)

    sa = ServiceAccount(name=name, filename=save_path)
    db.session.add(sa)
    db.session.commit()

    return jsonify({'status': 'Service Account uploaded', 'id': sa.id})

@app.route('/upload_user_list', methods=['POST'])
def upload_user_list():
    service_account_id = request.form.get('service_account_id')
    file = request.files.get('file')
    if not service_account_id or not file:
        return jsonify({'error': 'Missing service_account_id or file'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join('uploads', 'user_lists', filename)
    file.save(save_path)

    emails = set()
    with open(save_path, 'r', encoding='utf-8') as f:
        for line in f:
            email = line.strip()
            if email:
                emails.add(email.lower())

    existing_emails = {u.email.lower() for u in User.query.filter_by(service_account_id=int(service_account_id)).all()}
    new_emails = emails - existing_emails

    for email in new_emails:
        user = User(service_account_id=int(service_account_id), email=email)
        db.session.add(user)

    db.session.commit()
    return jsonify({'status': f'{len(new_emails)} users uploaded'})

@app.route('/upload_recipients', methods=['POST'])
def upload_recipients():
    campaign_id = request.form.get('campaign_id')
    file = request.files.get('file')
    if not campaign_id or not file:
        return jsonify({'error': 'Missing campaign_id or file'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join('uploads', 'recipient_lists', filename)
    file.save(save_path)

    emails = set()
    with open(save_path, 'r', encoding='utf-8') as f:
        for line in f:
            email = line.strip()
            if email:
                emails.add(email.lower())

    existing_emails = {r.email.lower() for r in CampaignRecipient.query.filter_by(campaign_id=int(campaign_id)).all()}
    new_emails = emails - existing_emails

    for email in new_emails:
        recipient = CampaignRecipient(campaign_id=int(campaign_id), email=email)
        db.session.add(recipient)

    db.session.commit()
    return jsonify({'status': f'{len(new_emails)} recipients uploaded'})

@app.route('/create_campaign', methods=['POST'])
def create_campaign():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    campaign = Campaign(
        name=data.get('name'),
        subject=data.get('subject'),
        body_html=data.get('body_html'),
        send_type=data.get('send_type'),
        x_delay=data.get('x_delay', None),
        send_speed=data.get('send_speed'),
        emails_per_user=data.get('emails_per_user'),
        test_email=data.get('test_email'),
        test_every=data.get('test_every'),
        headers_json=json.dumps(data.get('headers', []))
    )

    db.session.add(campaign)
    db.session.commit()

    user_ids = data.get('user_ids', [])
    for user_id in user_ids:
        campaign_user = CampaignUser(campaign_id=campaign.id, user_id=user_id)
        db.session.add(campaign_user)

    db.session.commit()
    return jsonify({'status': 'Campaign created', 'id': campaign.id})

@app.route('/api/service_accounts', methods=['GET'])
def list_service_accounts():
    accounts = ServiceAccount.query.all()
    return jsonify([{"id": sa.id, "name": sa.name} for sa in accounts])

@app.route('/api/campaigns', methods=['GET'])
def list_campaigns():
    campaigns = Campaign.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in campaigns])

@app.route('/users', methods=['GET'])
def list_users():
    service_account_id = request.args.get('service_account_id')
    if not service_account_id:
        return jsonify({'error': 'Missing service_account_id'}), 400
    users = User.query.filter_by(service_account_id=service_account_id).all()
    return jsonify([{"id": u.id, "email": u.email} for u in users])

@app.route('/recipients', methods=['GET'])
def list_recipients():
    campaign_id = request.args.get('campaign_id')
    if not campaign_id:
        return jsonify({'error': 'Missing campaign_id'}), 400
    recipients = CampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    return jsonify([{"id": r.id, "email": r.email} for r in recipients])

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    open('logs/campaign.log', 'w').close()
    return jsonify({"status": "Logs Cleared"})

@app.route('/api/dashboard_campaigns', methods=['GET'])
def dashboard_campaigns():
    campaigns = Campaign.query.all()
    result = []
    for campaign in campaigns:
        sent_count = CampaignLog.query.filter_by(campaign_id=campaign.id, status='SUCCESS').count()
        failed_count = CampaignLog.query.filter_by(campaign_id=campaign.id, status='FAILED').count()
        status = "Running" if worker and worker.campaign_id == campaign.id and worker.running else "Idle"
        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "sent": sent_count,
            "failed": failed_count,
            "status": status
        })
    return jsonify(result)

@app.route('/api/dashboard_service_accounts', methods=['GET'])
def dashboard_service_accounts():
    accounts = ServiceAccount.query.all()
    result = []
    for account in accounts:
        result.append({
            "id": account.id,
            "name": account.name,
            "quota": "Unlimited"
        })
    return jsonify(result)

@app.route('/send_test_email', methods=['POST'])
def send_test_email_route():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    service_account = ServiceAccount.query.get(data.get('service_account_id'))
    user = User.query.get(data.get('user_id'))

    if not service_account or not user:
        return jsonify({'error': 'Invalid Service Account or User'}), 400

    service = create_gmail_service(user.email, service_account.filename)

    raw_headers = data.get('raw_headers', '')
    full_body = data.get('full_body', '')

    # Replace tags
    raw_headers = raw_headers.replace('[user-sender]', user.email)
    raw_headers = replace_tags(raw_headers, user.email)
    full_body = replace_tags(full_body, user.email)

    full_message = raw_headers.strip() + "\n\n" + full_body
    encoded_message = base64.urlsafe_b64encode(full_message.encode('utf-8')).decode('utf-8')

    try:
        response = service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        with open(log_file, 'a') as f:
            f.write(f"Sent test email to {user.email}: {response.get('id')}\n")
        return jsonify({'status': 'Email sent', 'message_id': response.get('id')})
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Failed to send test email to {user.email}: {str(e)}\n")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
