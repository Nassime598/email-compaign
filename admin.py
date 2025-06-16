from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import ServiceAccount, User, Campaign, CampaignRecipient, CampaignUser, CampaignLog

def setup_admin(app, db):
    admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
    admin.add_view(ModelView(ServiceAccount, db.session))
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Campaign, db.session))
    admin.add_view(ModelView(CampaignRecipient, db.session))
    admin.add_view(ModelView(CampaignUser, db.session))
    admin.add_view(ModelView(CampaignLog, db.session))
