from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except AttributeError:
            return False


class Institution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    contact_person = db.Column(db.String(120), default='')
    contact_email = db.Column(db.String(120), default='')
    notes = db.Column(db.Text, default='')


class Partnership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='prospective')
    objective = db.Column(db.Text, nullable=False)
    requested_support = db.Column(db.Text, default='')
    timeline = db.Column(db.String(120), default='')
    institution = db.relationship('Institution')


class ResearchProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lead = db.Column(db.String(120), nullable=False)
    phase = db.Column(db.String(50), nullable=False, default='pilot')
    status = db.Column(db.String(50), nullable=False, default='active')
    research_question = db.Column(db.Text, nullable=False)
    methods = db.Column(db.Text, default='')
    outputs = db.Column(db.Text, default='')
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)
    space = db.Column(db.String(100), nullable=False)
    booking_type = db.Column(db.String(100), nullable=False)
    start_dt = db.Column(db.DateTime, nullable=False)
    end_dt = db.Column(db.DateTime, nullable=False)
    lead_name = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, default='')
    project = db.relationship('ResearchProject')


class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    portable = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default='available')
    owner = db.Column(db.String(120), default='Ideas Block / LMTA partnership')
    transfer_plan = db.Column(db.Text, default='')


class BudgetItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False)
    direction = db.Column(db.String(20), nullable=False)  # income or expense
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, default='')
    item_date = db.Column(db.Date, default=date.today)


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    body = db.Column(db.Text, nullable=False)
    decisions = db.Column(db.Text, default='')
    meeting_type = db.Column(db.String(80), default='steering')


class PolicyDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), default='1.0')


class RiskRegister(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    owner = db.Column(db.String(120), nullable=False)
    mitigation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open')


class RoadmapItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(50), nullable=False)  # phase_i / phase_ii
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    owner = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='planned')
    details = db.Column(db.Text, default='')


class ProtocolRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    principle = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    implementation = db.Column(db.Text, default='')


class DisseminationEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    format = db.Column(db.String(100), nullable=False)
    audience = db.Column(db.String(120), default='public')
    linked_project = db.Column(db.String(150), default='')
    notes = db.Column(db.Text, default='')


class MonthlyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(20), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
