from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declared_attr
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


db = SQLAlchemy()


class OwnershipMixin:
    @declared_attr
    def created_by_id(cls):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


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
    intellectual_contributions = db.Column(db.Text, default='')
    renewal_intention = db.Column(db.String(50), default='')
    institution = db.relationship('Institution')


class ResearchProject(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lead = db.Column(db.String(120), nullable=False)
    phase = db.Column(db.String(50), nullable=False, default='pilot')
    status = db.Column(db.String(50), nullable=False, default='active')
    domain = db.Column(db.String(30), nullable=False, default='research')
    research_question = db.Column(db.Text, nullable=False)
    methods = db.Column(db.Text, default='')
    outputs = db.Column(db.Text, default='')
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    budget_allocation = db.Column(db.Float, default=0.0)
    memberships = db.relationship('ProjectMembership', backref='project', lazy='dynamic')
    milestones = db.relationship('Milestone', backref='project', lazy='dynamic', order_by='Milestone.target_date')
    sessions = db.relationship('ResearchSession', lazy='dynamic', foreign_keys='ResearchSession.project_id', overlaps='project')


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


class Facility(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    capacity = db.Column(db.Integer, default=0)
    floor_area = db.Column(db.String(30), default='')
    location = db.Column(db.String(200), default='')
    modes = db.Column(db.Text, default='')
    characteristics = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='active')
    equipment_items = db.relationship('Equipment', backref='facility', lazy='dynamic')


class Equipment(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    portable = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default='available')
    owner = db.Column(db.String(120), default='Ideas Block / LMTA partnership')
    transfer_plan = db.Column(db.Text, default='')
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=True)


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
    working_group_id = db.Column(db.Integer, db.ForeignKey('working_group.id'), nullable=True)
    working_group = db.relationship('WorkingGroup')
    proposals = db.relationship('ProposalRecord', lazy='dynamic', foreign_keys='ProposalRecord.meeting_id')


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
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)


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
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=True)
    notes = db.Column(db.Text, default='')
    location = db.Column(db.String(200), default='')
    project_ref = db.relationship('ResearchProject')


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
    meeting = db.relationship('Meeting', overlaps='proposals')


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.relationship('User')


class WorkingGroup(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    focus = db.Column(db.String(200), default='')
    status = db.Column(db.String(30), default='active')
    memberships = db.relationship('WorkingGroupMembership', backref='group', lazy='dynamic')


class WorkingGroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wg_id = db.Column(db.Integer, db.ForeignKey('working_group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(80), default='member')
    user = db.relationship('User')


class ProjectMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(80), default='contributor')
    user = db.relationship('User')


class Milestone(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), default='pending')
    description = db.Column(db.Text, default='')
    url = db.Column(db.String(500), default='')


class Task(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='todo')
    priority = db.Column(db.String(20), default='normal')
    domain = db.Column(db.String(30), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'), nullable=True)
    url = db.Column(db.String(500), default='')
    assignee = db.relationship('User', foreign_keys=[assigned_to_id])
    milestone = db.relationship('Milestone')


class ConstitutionDocument(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), default='1.0')
    effective_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), default='active')


class Poll(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    poll_type = db.Column(db.String(20), default='single')
    status = db.Column(db.String(30), default='open')
    deadline = db.Column(db.DateTime, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    public_token = db.Column(db.String(64), nullable=True, unique=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    options = db.relationship('PollOption', backref='poll', order_by='PollOption.order', lazy='dynamic')
    votes = db.relationship('PollVote', backref='poll', lazy='dynamic')


class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    option_text = db.Column(db.String(300), nullable=False)
    order = db.Column(db.Integer, default=0)


class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    anon_token = db.Column(db.String(64), nullable=True)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    option = db.relationship('PollOption')


class LegacyTask(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    owner = db.Column(db.String(120), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), default='pending')
    priority = db.Column(db.String(20), default='normal')
    notes = db.Column(db.Text, default='')
    url = db.Column(db.String(500), default='')


class PollToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    label = db.Column(db.String(200), default='')
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    poll = db.relationship('Poll')


class CallForSubmission(OwnershipMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(300), default='')
    venue_type = db.Column(db.String(50), nullable=False, default='conference')
    area = db.Column(db.Text, default='')
    description = db.Column(db.Text, default='')
    deadline_status = db.Column(db.String(30), default='unknown-current')
    known_deadline = db.Column(db.Date, nullable=True)
    source_url = db.Column(db.String(500), default='')
    guidelines = db.Column(db.Text, default='')
    recurrence = db.Column(db.String(20), nullable=False, default='none')
    last_verified_at = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship('CallSubscription', backref='call', lazy='dynamic',
                                    cascade='all, delete-orphan')


class CallSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('call_for_submission.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    __table_args__ = (db.UniqueConstraint('call_id', 'user_id', name='uq_call_subscription'),)
