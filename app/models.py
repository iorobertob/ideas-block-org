from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


db = SQLAlchemy()


class OwnershipMixin:
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False


class Institution(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    contact_person = db.Column(db.String(120), default='')
    contact_email = db.Column(db.String(120), default='')
    notes = db.Column(db.Text, default='')


class Partnership(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='prospective')
    objective = db.Column(db.Text, nullable=False)
    requested_support = db.Column(db.Text, default='')
    timeline = db.Column(db.String(120), default='')
    institution = db.relationship('Institution')


class ResearchProject(OwnershipMixin, db.Model):
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


class Booking(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)
    space = db.Column(db.String(100), nullable=False)
    booking_type = db.Column(db.String(100), nullable=False)
    start_dt = db.Column(db.DateTime, nullable=False)
    end_dt = db.Column(db.DateTime, nullable=False)
    lead_name = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, default='')
    project = db.relationship('ResearchProject')


class Equipment(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    portable = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default='available')
    owner = db.Column(db.String(120), default='Ideas Block / LMTA partnership')
    transfer_plan = db.Column(db.Text, default='')


class BudgetItem(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False)
    direction = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, default='')
    item_date = db.Column(db.Date, default=date.today)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=True)
    project = db.relationship('ResearchProject')


class Meeting(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    body = db.Column(db.Text, nullable=False)
    decisions = db.Column(db.Text, default='')
    meeting_type = db.Column(db.String(80), default='steering')


class PolicyDocument(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), default='1.0')


class RiskRegister(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    owner = db.Column(db.String(120), nullable=False)
    mitigation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open')


class RoadmapItem(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    owner = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='planned')
    details = db.Column(db.Text, default='')


class ProtocolRule(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    principle = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    implementation = db.Column(db.Text, default='')


class DisseminationEvent(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    format = db.Column(db.String(100), nullable=False)
    audience = db.Column(db.String(120), default='public')
    linked_project = db.Column(db.String(150), default='')
    notes = db.Column(db.Text, default='')


class MonthlyReport(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(20), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(30), nullable=False)
    field_changed = db.Column(db.String(100), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')


class ResearchSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    facilitator = db.Column(db.String(120), nullable=False)
    participants = db.Column(db.Text, default='')
    methods_used = db.Column(db.Text, default='')
    observations = db.Column(db.Text, default='')
    open_questions = db.Column(db.Text, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    project = db.relationship('ResearchProject')


class ProposalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    proposal_text = db.Column(db.Text, nullable=False)
    proposer = db.Column(db.String(120), nullable=False)
    outcome = db.Column(db.String(30), nullable=False, default='pending')
    votes_for = db.Column(db.Integer, default=0)
    votes_against = db.Column(db.Integer, default=0)
    dissenting_notes = db.Column(db.Text, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    meeting = db.relationship('Meeting')


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.relationship('User')
