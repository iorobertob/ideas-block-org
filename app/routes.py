from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory, jsonify
from datetime import datetime, date
import calendar as cal_module
import os
import uuid
from sqlalchemy import func
from werkzeug.utils import secure_filename
from .models import (
    db, User, Institution, Partnership, ResearchProject, Booking, Equipment,
    BudgetItem, Meeting, PolicyDocument, RiskRegister, RoadmapItem,
    ProtocolRule, DisseminationEvent, MonthlyReport,
    AuditLog, ResearchSession, ProposalRecord, Attachment,
    WorkingGroup, WorkingGroupMembership, ProjectMembership,
    Milestone, Task, Facility, ConstitutionDocument,
    Poll, PollOption, PollVote, PollToken,
    LegacyTask
)


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def current_user():
    uid = session.get('user_id')
    if uid:
        return db.session.get(User, uid)
    return None


def login_required():
    return current_user() is not None


def is_manager(user=None):
    user = user or current_user()
    return bool(user and user.role in {'admin', 'director', 'coordinator'})


def can_edit_record(obj, user=None):
    user = user or current_user()
    if not user:
        return False
    if isinstance(obj, User):
        return is_manager(user) or obj.id == user.id
    return is_manager(user) or getattr(obj, 'created_by_id', None) == user.id


# ─────────────────────────────────────────────
# Field helpers
# ─────────────────────────────────────────────

def parse_date(v):
    return datetime.strptime(v, '%Y-%m-%d').date() if v else None


def parse_dt(v):
    return datetime.strptime(v, '%Y-%m-%dT%H:%M') if v else None


def format_value(value, field_type):
    if value is None:
        return ''
    if field_type == 'date':
        return value.strftime('%Y-%m-%d') if hasattr(value, 'strftime') else value
    if field_type == 'datetime':
        return value.strftime('%Y-%m-%dT%H:%M') if hasattr(value, 'strftime') else value
    if field_type == 'checkbox':
        return bool(value)
    return value


def assign_field(obj, field, raw_value):
    field_type = field.get('type', 'text')
    name = field['name']
    if field_type == 'date':
        setattr(obj, name, parse_date(raw_value))
    elif field_type == 'datetime':
        setattr(obj, name, parse_dt(raw_value))
    elif field_type == 'float':
        setattr(obj, name, float(raw_value) if raw_value else 0.0)
    elif field_type == 'int':
        setattr(obj, name, int(raw_value) if raw_value else None)
    elif field_type == 'checkbox':
        setattr(obj, name, name in request.form)
    elif field_type == 'url':
        setattr(obj, name, raw_value.strip())
    elif field_type == 'password':
        if raw_value:
            obj.set_password(raw_value)
    elif field_type == 'select' and field.get('nullable'):
        setattr(obj, name, int(raw_value) if raw_value else None)
    else:
        setattr(obj, name, raw_value)


def select_options_for(field_name):
    if field_name == 'project_id':
        return [(str(p.id), p.title) for p in ResearchProject.query.order_by(ResearchProject.title).all()]
    if field_name == 'institution_id':
        return [(str(i.id), i.name) for i in Institution.query.order_by(Institution.name).all()]
    if field_name == 'meeting_id':
        return [(str(m.id), f"{m.meeting_date} · {m.title}") for m in Meeting.query.order_by(Meeting.meeting_date.desc()).all()]
    if field_name == 'facility_id':
        return [(str(f.id), f.name) for f in Facility.query.order_by(Facility.name).all()]
    if field_name == 'assigned_to_id':
        return [(str(u.id), f"{u.name} ({u.role})") for u in User.query.order_by(User.name).all()]
    if field_name == 'milestone_id':
        return [(str(m.id), f"{m.title} [{m.project.title if m.project else '?'}]") for m in Milestone.query.all()]
    if field_name == 'working_group_id':
        return [(str(wg.id), wg.name) for wg in WorkingGroup.query.order_by(WorkingGroup.name).all()]
    return []


def _capture_values(obj, config):
    vals = {}
    for field in config['fields']:
        n = field['name']
        if n != 'password':
            vals[n] = str(getattr(obj, n, '') or '')
    return vals


def _add_audit_log(entity_type, entity_id, action, field_changed=None, old_value=None, new_value=None):
    user = current_user()
    db.session.add(AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user.id if user else None,
        action=action,
        field_changed=field_changed,
        old_value=old_value,
        new_value=new_value,
    ))


def _log_field_changes(entity_type, entity_id, old_vals, new_vals):
    user = current_user()
    uid = user.id if user else None
    for fname, old_v in old_vals.items():
        new_v = new_vals.get(fname, '')
        if old_v != new_v:
            db.session.add(AuditLog(
                entity_type=entity_type, entity_id=entity_id,
                user_id=uid, action='update',
                field_changed=fname, old_value=old_v, new_value=new_v
            ))


# ─────────────────────────────────────────────
# RECORD_CONFIG
# ─────────────────────────────────────────────

RECORD_CONFIG = {
    'users': {
        'model': User,
        'title': 'Users',
        'singular': 'User',
        'list_endpoint': 'users',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'},
            {'name': 'email', 'label': 'Email', 'type': 'email'},
            {'name': 'role', 'label': 'Role', 'type': 'select', 'choices': [('member', 'member'), ('coordinator', 'coordinator'), ('director', 'director'), ('admin', 'admin')]},
            {'name': 'password', 'label': 'Reset Password', 'type': 'password'},
        ],
    },
    'projects': {
        'model': ResearchProject,
        'title': 'Projects',
        'singular': 'Project',
        'list_endpoint': 'projects',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'lead', 'label': 'Lead'},
            {'name': 'domain', 'label': 'Domain', 'type': 'select', 'choices': [('research', 'Research'), ('program', 'Program'), ('operations', 'Operations')]},
            {'name': 'phase', 'label': 'Phase', 'type': 'select', 'choices': [('phase_i', 'Phase I'), ('phase_ii', 'Phase II'), ('pilot', 'Pilot')]},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('active', 'active'), ('planned', 'planned'), ('completed', 'completed')]},
            {'name': 'research_question', 'label': 'Research question / objective', 'type': 'textarea'},
            {'name': 'methods', 'label': 'Methods / approach', 'type': 'textarea'},
            {'name': 'outputs', 'label': 'Outputs', 'type': 'textarea'},
            {'name': 'budget_allocation', 'label': 'Budget allocation (€)', 'type': 'float'},
            {'name': 'start_date', 'label': 'Start date', 'type': 'date'},
            {'name': 'end_date', 'label': 'End date', 'type': 'date'},
        ],
    },
    'bookings': {
        'model': Booking,
        'title': 'Bookings',
        'singular': 'Booking',
        'list_endpoint': 'bookings',
        'summary': lambda o: f"{o.space} · {o.booking_type}",
        'fields': [
            {'name': 'project_id', 'label': 'Project', 'type': 'select', 'options_provider': select_options_for},
            {'name': 'space', 'label': 'Space'},
            {'name': 'booking_type', 'label': 'Booking type'},
            {'name': 'start_dt', 'label': 'Start', 'type': 'datetime'},
            {'name': 'end_dt', 'label': 'End', 'type': 'datetime'},
            {'name': 'lead_name', 'label': 'Lead name'},
            {'name': 'notes', 'label': 'Notes', 'type': 'textarea'},
        ],
    },
    'equipment': {
        'model': Equipment,
        'title': 'Equipment',
        'singular': 'Equipment item',
        'list_endpoint': 'equipment',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'}, {'name': 'category', 'label': 'Category'},
            {'name': 'portable', 'label': 'Portable', 'type': 'checkbox'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('available', 'available'), ('in_use', 'in_use'), ('maintenance', 'maintenance'), ('reserved', 'reserved')]},
            {'name': 'owner', 'label': 'Owner'},
            {'name': 'transfer_plan', 'label': 'Transfer plan', 'type': 'textarea'},
            {'name': 'facility_id', 'label': 'Facility', 'type': 'select', 'nullable': True,
             'options_provider': lambda fn: [('', '— none —')] + select_options_for(fn)},
        ],
    },
    'budget': {
        'model': BudgetItem,
        'title': 'Budget',
        'singular': 'Budget item',
        'list_endpoint': 'budget',
        'summary': lambda o: f"{o.category} · €{o.amount}",
        'fields': [
            {'name': 'category', 'label': 'Category'},
            {'name': 'direction', 'label': 'Direction', 'type': 'select', 'choices': [('income', 'income'), ('expense', 'expense')]},
            {'name': 'amount', 'label': 'Amount', 'type': 'float'},
            {'name': 'note', 'label': 'Note', 'type': 'textarea'},
            {'name': 'item_date', 'label': 'Item date', 'type': 'date'},
            {'name': 'project_id', 'label': 'Project (optional)', 'type': 'select', 'nullable': True,
             'options_provider': lambda fn: [('', '— none —')] + select_options_for(fn)},
        ],
    },
    'governance': {
        'model': Meeting,
        'title': 'Governance',
        'singular': 'Meeting',
        'list_endpoint': 'governance',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'meeting_date', 'label': 'Meeting date', 'type': 'date'},
            {'name': 'meeting_type', 'label': 'Meeting type', 'type': 'select', 'choices': [('steering', 'steering'), ('operations', 'operations'), ('working_group', 'working_group'), ('curating', 'curating'), ('partnership', 'partnership')]},
            {'name': 'working_group_id', 'label': 'Working Group', 'type': 'select', 'nullable': True,
             'options_provider': lambda fn: [('', '— none —')] + select_options_for(fn)},
            {'name': 'body', 'label': 'Body', 'type': 'textarea'},
            {'name': 'decisions', 'label': 'Decisions', 'type': 'textarea'},
        ],
    },
    'institutions': {
        'model': Institution,
        'title': 'Institutions',
        'singular': 'Institution',
        'list_endpoint': 'partnerships',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'}, {'name': 'category', 'label': 'Category'},
            {'name': 'contact_person', 'label': 'Contact person'},
            {'name': 'contact_email', 'label': 'Contact email', 'type': 'email'},
            {'name': 'notes', 'label': 'Notes', 'type': 'textarea'},
        ],
    },
    'partnerships': {
        'model': Partnership,
        'title': 'Partnerships',
        'singular': 'Partnership',
        'list_endpoint': 'partnerships',
        'summary': lambda o: o.institution.name if o.institution else f"Partnership #{o.id}",
        'fields': [
            {'name': 'institution_id', 'label': 'Institution', 'type': 'select', 'options_provider': select_options_for},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('prospective', 'prospective'), ('active', 'active'), ('closed', 'closed')]},
            {'name': 'objective', 'label': 'Objective', 'type': 'textarea'},
            {'name': 'requested_support', 'label': 'Requested support', 'type': 'textarea'},
            {'name': 'intellectual_contributions', 'label': 'Intellectual contributions', 'type': 'textarea'},
            {'name': 'renewal_intention', 'label': 'Renewal intention', 'type': 'select', 'choices': [('', '—'), ('yes', 'yes'), ('no', 'no'), ('maybe', 'maybe')]},
            {'name': 'timeline', 'label': 'Timeline'},
        ],
    },
    'protocol': {
        'model': ProtocolRule,
        'title': 'Protocol',
        'singular': 'Protocol rule',
        'list_endpoint': 'protocol',
        'summary': lambda o: o.principle,
        'fields': [
            {'name': 'principle', 'label': 'Principle'},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'implementation', 'label': 'Implementation', 'type': 'textarea'},
        ],
    },
    'policies': {
        'model': PolicyDocument,
        'title': 'Policies',
        'singular': 'Policy document',
        'list_endpoint': 'policies',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'}, {'name': 'category', 'label': 'Category'},
            {'name': 'version', 'label': 'Version'},
            {'name': 'content', 'label': 'Content', 'type': 'textarea'},
        ],
    },
    'risks': {
        'model': RiskRegister,
        'title': 'Risks',
        'singular': 'Risk',
        'list_endpoint': 'risks',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'severity', 'label': 'Severity', 'type': 'select', 'choices': [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]},
            {'name': 'owner', 'label': 'Owner'},
            {'name': 'mitigation', 'label': 'Mitigation', 'type': 'textarea'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('open', 'open'), ('monitoring', 'monitoring'), ('closed', 'closed')]},
        ],
    },
    'roadmap': {
        'model': RoadmapItem,
        'title': 'Roadmap',
        'singular': 'Roadmap item',
        'list_endpoint': 'roadmap',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'phase', 'label': 'Phase', 'type': 'select', 'choices': [('phase_i', 'Phase I'), ('phase_ii', 'Phase II')]},
            {'name': 'title', 'label': 'Title'},
            {'name': 'year', 'label': 'Year', 'type': 'int'},
            {'name': 'owner', 'label': 'Owner'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('planned', 'planned'), ('in_progress', 'in_progress'), ('completed', 'completed')]},
            {'name': 'details', 'label': 'Details', 'type': 'textarea'},
            {'name': 'start_date', 'label': 'Start date', 'type': 'date'},
            {'name': 'end_date', 'label': 'End date', 'type': 'date'},
        ],
    },
    'events': {
        'model': DisseminationEvent,
        'title': 'Events',
        'singular': 'Dissemination event',
        'list_endpoint': 'events',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'event_date', 'label': 'Event date', 'type': 'date'},
            {'name': 'format', 'label': 'Format'},
            {'name': 'audience', 'label': 'Audience'},
            {'name': 'location', 'label': 'Location'},
            {'name': 'project_id', 'label': 'Project', 'type': 'select', 'nullable': True,
             'options_provider': lambda fn: [('', '— none —')] + select_options_for(fn)},
            {'name': 'notes', 'label': 'Notes', 'type': 'textarea'},
        ],
    },
    'reports': {
        'model': MonthlyReport,
        'title': 'Reports',
        'singular': 'Monthly report',
        'list_endpoint': 'reports',
        'summary': lambda o: o.month,
        'fields': [
            {'name': 'month', 'label': 'Month'},
            {'name': 'summary', 'label': 'Summary', 'type': 'textarea'},
        ],
    },
    'sessions': {
        'model': ResearchSession,
        'title': 'Research Sessions',
        'singular': 'Research session',
        'list_endpoint': 'projects',
        'summary': lambda o: f"{o.project.title if o.project else '?'} · {o.session_date}",
        'fields': [
            {'name': 'project_id', 'label': 'Project', 'type': 'select', 'options_provider': select_options_for},
            {'name': 'session_date', 'label': 'Session date', 'type': 'date'},
            {'name': 'facilitator', 'label': 'Facilitator'},
            {'name': 'participants', 'label': 'Participants', 'type': 'textarea'},
            {'name': 'methods_used', 'label': 'Methods used', 'type': 'textarea'},
            {'name': 'observations', 'label': 'Observations', 'type': 'textarea'},
            {'name': 'open_questions', 'label': 'Open questions', 'type': 'textarea'},
        ],
    },
    'proposals': {
        'model': ProposalRecord,
        'title': 'Proposals',
        'singular': 'Proposal',
        'list_endpoint': 'governance',
        'summary': lambda o: (o.proposal_text[:80] + '...') if len(o.proposal_text) > 80 else o.proposal_text,
        'fields': [
            {'name': 'meeting_id', 'label': 'Meeting', 'type': 'select', 'options_provider': select_options_for},
            {'name': 'proposal_text', 'label': 'Proposal', 'type': 'textarea'},
            {'name': 'proposer', 'label': 'Proposer'},
            {'name': 'outcome', 'label': 'Outcome', 'type': 'select', 'choices': [('pending', 'pending'), ('approved', 'approved'), ('rejected', 'rejected'), ('deferred', 'deferred')]},
            {'name': 'votes_for', 'label': 'Votes for', 'type': 'int'},
            {'name': 'votes_against', 'label': 'Votes against', 'type': 'int'},
            {'name': 'dissenting_notes', 'label': 'Dissenting notes', 'type': 'textarea'},
        ],
    },
    'tasks': {
        'model': Task,
        'title': 'Tasks',
        'singular': 'Task',
        'list_endpoint': 'tasks',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'domain', 'label': 'Domain', 'type': 'select', 'choices': [('', '— unclassified —'), ('research', 'Research'), ('program', 'Program'), ('operations', 'Operations')]},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('todo', 'To do'), ('in_progress', 'In progress'), ('done', 'Done'), ('blocked', 'Blocked')]},
            {'name': 'priority', 'label': 'Priority', 'type': 'select', 'choices': [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]},
            {'name': 'due_date', 'label': 'Due date', 'type': 'date'},
            {'name': 'entity_type', 'label': 'Linked to (type)', 'type': 'select', 'choices': [
                ('', '— none —'), ('projects', 'Project'), ('events', 'Event'),
                ('working_groups', 'Working Group'), ('governance', 'Meeting'),
                ('partnerships', 'Partnership'), ('legacy_tasks', 'Legacy Task'),
            ]},
            {'name': 'entity_id', 'label': 'Linked to (ID)', 'type': 'int'},
            {'name': 'url', 'label': 'Reference URL', 'type': 'url'},
            {'name': 'assigned_to_id', 'label': 'Assignee', 'type': 'select', 'nullable': True,
             'options_provider': lambda fn: [('', '— unassigned —')] + select_options_for(fn)},
        ],
    },
    'milestones': {
        'model': Milestone,
        'title': 'Milestones',
        'singular': 'Milestone',
        'list_endpoint': 'projects',
        'summary': lambda o: f"{o.title} [{o.project.title if o.project else '?'}]",
        'fields': [
            {'name': 'project_id', 'label': 'Project', 'type': 'select', 'options_provider': select_options_for},
            {'name': 'title', 'label': 'Title'},
            {'name': 'target_date', 'label': 'Target date', 'type': 'date'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('pending', 'pending'), ('reached', 'reached'), ('missed', 'missed')]},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'url', 'label': 'Reference URL', 'type': 'url'},
        ],
    },
    'facilities': {
        'model': Facility,
        'title': 'Facilities',
        'singular': 'Facility',
        'list_endpoint': 'facilities',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'capacity', 'label': 'Capacity (persons)', 'type': 'int'},
            {'name': 'floor_area', 'label': 'Floor area'},
            {'name': 'location', 'label': 'Location'},
            {'name': 'modes', 'label': 'Modes (e.g. rehearsal, seminar, presentation)', 'type': 'textarea'},
            {'name': 'characteristics', 'label': 'Characteristics (acoustics, lighting, etc.)', 'type': 'textarea'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('active', 'active'), ('maintenance', 'maintenance'), ('closed', 'closed')]},
        ],
    },
    'working_groups': {
        'model': WorkingGroup,
        'title': 'Working Groups',
        'singular': 'Working group',
        'list_endpoint': 'working_groups',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'},
            {'name': 'focus', 'label': 'Focus area'},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('active', 'active'), ('archived', 'archived')]},
        ],
    },
    'legacy_tasks': {
        'model': LegacyTask,
        'title': 'Legacy Tasks',
        'singular': 'Legacy task',
        'list_endpoint': 'legacy',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'category', 'label': 'Category', 'type': 'select', 'choices': [
                ('equipment', 'Equipment Transfer'),
                ('knowledge', 'Knowledge Transfer'),
                ('partnership', 'Partnership Handoff'),
                ('funding', 'Funding & Finance'),
                ('governance', 'Governance & Documentation'),
                ('research', 'Research Output'),
            ]},
            {'name': 'owner', 'label': 'Owner'},
            {'name': 'deadline', 'label': 'Deadline', 'type': 'date'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [
                ('pending', 'Pending'), ('in_progress', 'In progress'), ('done', 'Done'), ('blocked', 'Blocked'),
            ]},
            {'name': 'priority', 'label': 'Priority', 'type': 'select', 'choices': [
                ('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent'),
            ]},
            {'name': 'description', 'label': 'Description', 'type': 'textarea'},
            {'name': 'notes', 'label': 'Notes / progress', 'type': 'textarea'},
            {'name': 'url', 'label': 'Reference URL', 'type': 'url'},
        ],
    },
    'constitution': {
        'model': ConstitutionDocument,
        'title': 'Constitution & Statutes',
        'singular': 'Constitutional document',
        'list_endpoint': 'constitution',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'},
            {'name': 'category', 'label': 'Category', 'type': 'select', 'choices': [
                ('philosophy', 'Philosophy'), ('constitution', 'Constitution'), ('statute', 'Statute'),
                ('charter', 'Charter'), ('values', 'Core Values'), ('manifesto', 'Manifesto')]},
            {'name': 'version', 'label': 'Version'},
            {'name': 'effective_date', 'label': 'Effective date', 'type': 'date'},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('draft', 'Draft'), ('active', 'Active'), ('superseded', 'Superseded')]},
            {'name': 'content', 'label': 'Content', 'type': 'textarea'},
        ],
    },
}


def apply_form_to_record(obj, config):
    for field in config['fields']:
        if field['name'] == 'role' and isinstance(obj, User) and not is_manager() and obj.id == current_user().id:
            continue
        raw_value = request.form.get(field['name'], '')
        assign_field(obj, field, raw_value)


def create_record(kind):
    config = RECORD_CONFIG[kind]
    model = config['model']
    obj = model()
    apply_form_to_record(obj, config)
    if hasattr(obj, 'created_by_id'):
        obj.created_by_id = current_user().id
    if kind == 'bookings':
        conflict = Booking.query.filter(
            Booking.space == obj.space,
            Booking.id != obj.id,
            Booking.start_dt < obj.end_dt,
            Booking.end_dt > obj.start_dt
        ).first()
        if conflict:
            flash(f'Conflict detected with booking #{conflict.id} in {obj.space}.', 'danger')
            return False
        # Protocol enforcement: research-first scheduling
        if obj.start_dt:
            weekday = obj.start_dt.weekday()  # 0=Mon, 6=Sun
            hour = obj.start_dt.hour
            research_types = {'research session', 'residency', 'rehearsal', 'workshop', 'studio session', 'experiment', 'practice'}
            booking_type_lower = (obj.booking_type or '').lower()
            is_research = any(rt in booking_type_lower for rt in research_types)
            if weekday < 5 and 9 <= hour < 17 and not is_research:
                flash(
                    f'Protocol notice: "{obj.booking_type}" is scheduled during protected research hours (weekday 9–17). '
                    'Per the Research-First Scheduling Protocol, weekday daytime blocks are reserved for research activities. '
                    'Booking created — please document the reason in the notes.',
                    'warning'
                )
    db.session.add(obj)
    db.session.flush()
    _add_audit_log(kind, obj.id, 'create')
    db.session.commit()
    flash(f"{config['singular']} created.", 'success')
    return True


# ─────────────────────────────────────────────
# Route registration
# ─────────────────────────────────────────────

def register_routes(app):

    @app.context_processor
    def inject_user():
        return {'current_user': current_user(), 'can_edit_record': can_edit_record, 'is_manager': is_manager()}

    # ── Dashboard ──

    @app.route('/')
    def index():
        if not login_required():
            return redirect(url_for('login'))
        income = db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='income').scalar()
        expense = db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='expense').scalar()
        overdue_count = Task.query.filter(
            Task.due_date < date.today(),
            Task.status.notin_(['done'])
        ).count()
        stats = {
            'projects': ResearchProject.query.count(),
            'bookings': Booking.query.count(),
            'equipment': Equipment.query.count(),
            'partners': Partnership.query.count(),
            'net_budget': round(income - expense, 2),
            'open_tasks': Task.query.filter(Task.status.in_(['todo', 'in_progress'])).count(),
            'overdue_tasks': overdue_count,
            'open_risks': RiskRegister.query.filter(RiskRegister.status != 'closed').count(),
        }
        upcoming = Booking.query.filter(Booking.start_dt >= datetime.utcnow()).order_by(Booking.start_dt.asc()).limit(6).all()
        meetings = Meeting.query.order_by(Meeting.meeting_date.desc()).limit(4).all()
        risks = RiskRegister.query.filter(RiskRegister.status != 'closed').order_by(RiskRegister.severity.desc()).limit(4).all()
        upcoming_events = DisseminationEvent.query.filter(DisseminationEvent.event_date >= date.today()).order_by(DisseminationEvent.event_date.asc()).limit(3).all()
        my_tasks = Task.query.filter_by(assigned_to_id=current_user().id).filter(Task.status.in_(['todo', 'in_progress'])).order_by(Task.due_date.asc()).limit(5).all() if current_user() else []
        open_polls = Poll.query.filter_by(status='open').order_by(Poll.id.desc()).limit(3).all()
        # Phase progress indicators
        ms_total = Milestone.query.count()
        ms_reached = Milestone.query.filter_by(status='reached').count()
        tasks_total = Task.query.count()
        tasks_done = Task.query.filter_by(status='done').count()
        risks_total = RiskRegister.query.count()
        risks_closed = RiskRegister.query.filter_by(status='closed').count()
        active_projects = ResearchProject.query.filter_by(status='active').all()
        phase_progress = {
            'milestones': {'done': ms_reached, 'total': ms_total},
            'tasks': {'done': tasks_done, 'total': tasks_total},
            'risks_resolved': {'done': risks_closed, 'total': risks_total},
        }
        # Legacy planning — urgent/overdue tasks
        legacy_urgent = LegacyTask.query.filter(
            LegacyTask.status.notin_(['done']),
            LegacyTask.priority.in_(['urgent', 'high'])
        ).order_by(LegacyTask.deadline.asc()).limit(5).all()
        legacy_total = LegacyTask.query.count()
        legacy_done = LegacyTask.query.filter_by(status='done').count()
        return render_template('dashboard.html', stats=stats, upcoming=upcoming, meetings=meetings,
                               risks=risks, upcoming_events=upcoming_events, my_tasks=my_tasks,
                               phase_progress=phase_progress, active_projects=active_projects,
                               open_polls=open_polls, legacy_urgent=legacy_urgent,
                               legacy_total=legacy_total, legacy_done=legacy_done)

    # ── Auth ──

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                flash('Welcome back.', 'success')
                return redirect(url_for('index'))
            flash('Invalid credentials.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logged out.', 'info')
        return redirect(url_for('login'))

    # ── Users ──

    @app.route('/users', methods=['GET', 'POST'])
    def users():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            if not is_manager():
                flash('You do not have permission to create users.', 'danger')
                return redirect(url_for('users'))
            create_record('users')
            return redirect(url_for('users'))
        return render_template('users.html', users=User.query.order_by(User.name).all())

    # ── Projects ──

    @app.route('/projects', methods=['GET', 'POST'])
    def projects():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('projects')
            return redirect(url_for('projects'))
        q = request.args.get('q', '').strip()
        status = request.args.get('status', '')
        phase = request.args.get('phase', '')
        domain = request.args.get('domain', '')
        query = ResearchProject.query
        if q:
            query = query.filter(
                ResearchProject.title.ilike(f'%{q}%') |
                ResearchProject.lead.ilike(f'%{q}%') |
                ResearchProject.research_question.ilike(f'%{q}%')
            )
        if status:
            query = query.filter_by(status=status)
        if phase:
            query = query.filter_by(phase=phase)
        if domain:
            query = query.filter_by(domain=domain)
        return render_template('projects.html',
                               projects=query.order_by(ResearchProject.start_date.desc()).all(),
                               q=q, status=status, phase=phase, domain=domain,
                               now_date=date.today())

    @app.route('/projects/<int:project_id>/add-member', methods=['POST'])
    def add_project_member(project_id):
        if not login_required():
            return redirect(url_for('login'))
        project = db.session.get(ResearchProject, project_id)
        if not project:
            abort(404)
        user_id = int(request.form.get('user_id', 0))
        role = request.form.get('role', 'contributor')
        if user_id and not ProjectMembership.query.filter_by(project_id=project_id, user_id=user_id).first():
            db.session.add(ProjectMembership(project_id=project_id, user_id=user_id, role=role))
            db.session.commit()
            flash('Member added.', 'success')
        return redirect(url_for('record_detail', kind='projects', record_id=project_id))

    @app.route('/projects/<int:project_id>/remove-member/<int:mid>', methods=['POST'])
    def remove_project_member(project_id, mid):
        if not login_required() or not is_manager():
            abort(403)
        m = db.session.get(ProjectMembership, mid)
        if m and m.project_id == project_id:
            db.session.delete(m)
            db.session.commit()
            flash('Member removed.', 'info')
        return redirect(url_for('record_detail', kind='projects', record_id=project_id))

    @app.route('/projects/<int:project_id>/add-milestone', methods=['POST'])
    def add_milestone(project_id):
        if not login_required():
            return redirect(url_for('login'))
        m = Milestone(
            project_id=project_id,
            title=request.form.get('title', ''),
            target_date=parse_date(request.form.get('target_date')),
            status=request.form.get('status', 'pending'),
            description=request.form.get('description', ''),
            created_by_id=current_user().id,
        )
        db.session.add(m)
        db.session.commit()
        flash('Milestone added.', 'success')
        return redirect(url_for('record_detail', kind='projects', record_id=project_id))

    # ── Bookings ──

    @app.route('/bookings', methods=['GET', 'POST'])
    def bookings():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('bookings')
            return redirect(url_for('bookings'))
        q = request.args.get('q', '').strip()
        space = request.args.get('space', '').strip()
        query = Booking.query
        if q:
            query = query.filter(
                Booking.space.ilike(f'%{q}%') |
                Booking.booking_type.ilike(f'%{q}%') |
                Booking.lead_name.ilike(f'%{q}%')
            )
        if space:
            query = query.filter_by(space=space)
        spaces = [r[0] for r in db.session.query(Booking.space).distinct().order_by(Booking.space).all()]
        return render_template('bookings.html',
                               bookings=query.order_by(Booking.start_dt.asc()).all(),
                               projects=ResearchProject.query.order_by(ResearchProject.title).all(),
                               spaces=spaces, q=q, space=space)

    @app.route('/bookings/calendar')
    def booking_calendar():
        if not login_required():
            return redirect(url_for('login'))
        today = date.today()
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
        month = max(1, min(12, month))
        start = datetime(year, month, 1)
        end = datetime(year + (month // 12), (month % 12) + 1, 1)
        month_bookings = Booking.query.filter(Booking.start_dt >= start, Booking.start_dt < end).all()
        day_bookings = {}
        for b in month_bookings:
            d = b.start_dt.day
            day_bookings.setdefault(d, []).append(b)
        weeks = cal_module.monthcalendar(year, month)
        month_name = cal_module.month_name[month]
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        return render_template('booking_calendar.html',
                               weeks=weeks, day_bookings=day_bookings, year=year, month=month,
                               month_name=month_name, prev_year=prev_year, prev_month=prev_month,
                               next_year=next_year, next_month=next_month, today=today,
                               total_bookings=len(month_bookings))

    # ── Equipment ──

    @app.route('/equipment', methods=['GET', 'POST'])
    def equipment():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('equipment')
            return redirect(url_for('equipment'))
        q = request.args.get('q', '').strip()
        status = request.args.get('status', '')
        category = request.args.get('category', '')
        query = Equipment.query
        if q:
            query = query.filter(Equipment.name.ilike(f'%{q}%') | Equipment.owner.ilike(f'%{q}%'))
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        categories = [r[0] for r in db.session.query(Equipment.category).distinct().order_by(Equipment.category).all()]
        all_equipment = Equipment.query.all()
        transfer_total = len(all_equipment)
        transfer_done = sum(1 for e in all_equipment if e.transfer_plan and e.transfer_plan.strip())
        return render_template('equipment.html',
                               equipment=query.order_by(Equipment.category, Equipment.name).all(),
                               categories=categories, q=q, status=status, category=category,
                               facilities=Facility.query.order_by(Facility.name).all(),
                               transfer_total=transfer_total, transfer_done=transfer_done)

    # ── Facilities ──

    @app.route('/facilities', methods=['GET', 'POST'])
    def facilities():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('facilities')
            return redirect(url_for('facilities'))
        return render_template('facilities.html',
                               facilities=Facility.query.order_by(Facility.name).all())

    # ── Budget ──

    @app.route('/budget', methods=['GET', 'POST'])
    def budget():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('budget')
            return redirect(url_for('budget'))
        items = BudgetItem.query.order_by(BudgetItem.item_date.desc()).all()
        income = sum(i.amount for i in items if i.direction == 'income')
        expense = sum(i.amount for i in items if i.direction == 'expense')
        project_map = {p.id: p.title for p in ResearchProject.query.all()}
        proj_budgets = {}
        for item in items:
            if item.project_id:
                if item.project_id not in proj_budgets:
                    proj_budgets[item.project_id] = {'title': project_map.get(item.project_id, f'Project #{item.project_id}'), 'income': 0.0, 'expense': 0.0}
                proj_budgets[item.project_id][item.direction] += item.amount
        project_breakdown = [
            {'title': v['title'], 'income': v['income'], 'expense': v['expense'], 'net': v['income'] - v['expense']}
            for v in proj_budgets.values()
        ]
        projects = ResearchProject.query.order_by(ResearchProject.title).all()
        return render_template('budget.html', items=items, income=income, expense=expense,
                               net=income - expense, project_breakdown=project_breakdown, projects=projects)

    # ── Governance ──

    @app.route('/governance', methods=['GET', 'POST'])
    def governance():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('governance')
            return redirect(url_for('governance'))
        wg_filter = request.args.get('wg', '')
        query = Meeting.query
        if wg_filter:
            query = query.filter_by(working_group_id=int(wg_filter))
        wgs = WorkingGroup.query.order_by(WorkingGroup.name).all()
        return render_template('governance.html',
                               meetings=query.order_by(Meeting.meeting_date.desc()).all(),
                               working_groups=wgs, wg_filter=wg_filter)

    # ── Partnerships ──

    @app.route('/partnerships', methods=['GET', 'POST'])
    def partnerships():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            form_name = request.form['form_name']
            create_record('institutions' if form_name == 'institution' else 'partnerships')
            return redirect(url_for('partnerships'))
        return render_template('partnerships.html',
                               institutions=Institution.query.order_by(Institution.name).all(),
                               partnerships=Partnership.query.order_by(Partnership.id.desc()).all())

    # ── Protocol & Policies ──

    @app.route('/protocol', methods=['GET', 'POST'])
    def protocol():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('protocol')
            return redirect(url_for('protocol'))
        return render_template('protocol.html',
                               rules=ProtocolRule.query.order_by(ProtocolRule.id).all(),
                               policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

    @app.route('/policies', methods=['GET', 'POST'])
    def policies():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('policies')
            return redirect(url_for('policies'))
        return render_template('policies.html',
                               policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

    # ── Risks ──

    @app.route('/risks', methods=['GET', 'POST'])
    def risks():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('risks')
            return redirect(url_for('risks'))
        q = request.args.get('q', '').strip()
        status = request.args.get('status', '')
        severity = request.args.get('severity', '')
        query = RiskRegister.query
        if q:
            query = query.filter(RiskRegister.title.ilike(f'%{q}%') | RiskRegister.owner.ilike(f'%{q}%'))
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        return render_template('risks.html',
                               risks=query.order_by(RiskRegister.severity.desc(), RiskRegister.id.desc()).all(),
                               q=q, status=status, severity=severity)

    # ── Roadmap ──

    @app.route('/roadmap', methods=['GET', 'POST'])
    def roadmap():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('roadmap')
            return redirect(url_for('roadmap'))
        items = RoadmapItem.query.order_by(RoadmapItem.year.asc(), RoadmapItem.phase.asc()).all()
        return render_template('roadmap.html', items=items)

    @app.route('/roadmap/timeline')
    def roadmap_timeline():
        if not login_required():
            return redirect(url_for('login'))
        items = RoadmapItem.query.order_by(RoadmapItem.year.asc(), RoadmapItem.phase.asc()).all()
        years = sorted(set(i.year for i in items)) if items else [date.today().year]
        # Group by year
        by_year = {}
        for item in items:
            by_year.setdefault(item.year, []).append(item)
        return render_template('roadmap_timeline.html', items=items, years=years, by_year=by_year)

    # ── Events ──

    @app.route('/events', methods=['GET', 'POST'])
    def events():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('events')
            return redirect(url_for('events'))
        return render_template('events.html',
                               events=DisseminationEvent.query.order_by(DisseminationEvent.event_date.desc()).all(),
                               projects=ResearchProject.query.order_by(ResearchProject.title).all())

    @app.route('/events/calendar')
    def events_calendar():
        if not login_required():
            return redirect(url_for('login'))
        today = date.today()
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
        month = max(1, min(12, month))
        month_events = DisseminationEvent.query.filter(
            func.strftime('%Y', DisseminationEvent.event_date) == str(year),
            func.strftime('%m', DisseminationEvent.event_date) == f'{month:02d}'
        ).all()
        day_events = {}
        for e in month_events:
            day_events.setdefault(e.event_date.day, []).append(e)
        weeks = cal_module.monthcalendar(year, month)
        month_name = cal_module.month_name[month]
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        return render_template('events_calendar.html',
                               weeks=weeks, day_events=day_events, year=year, month=month,
                               month_name=month_name, prev_year=prev_year, prev_month=prev_month,
                               next_year=next_year, next_month=next_month, today=today,
                               total_events=len(month_events))

    # ── Reports ──

    def _month_stats(year, month):
        """Gather activity statistics for a given year/month."""
        ym = f'{year}-{month:02d}'
        month_start = datetime(year, month, 1)
        last_day = cal_module.monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59)

        bookings = Booking.query.filter(
            Booking.start_dt >= month_start, Booking.start_dt <= month_end
        ).all()
        events = DisseminationEvent.query.filter(
            func.strftime('%Y-%m', DisseminationEvent.event_date) == ym
        ).all()
        sessions = ResearchSession.query.filter(
            func.strftime('%Y-%m', ResearchSession.session_date) == ym
        ).all()
        meetings = Meeting.query.filter(
            func.strftime('%Y-%m', Meeting.meeting_date) == ym
        ).all()
        meeting_ids = [m.id for m in meetings]
        proposals = ProposalRecord.query.filter(
            ProposalRecord.meeting_id.in_(meeting_ids)
        ).all() if meeting_ids else []
        approved = [p for p in proposals if p.outcome == 'approved']
        milestones_reached = Milestone.query.filter(
            func.strftime('%Y-%m', Milestone.target_date) == ym,
            Milestone.status == 'reached'
        ).all()
        tasks_done = Task.query.filter(
            func.strftime('%Y-%m', Task.due_date) == ym,
            Task.status == 'done'
        ).all()
        risks_open = RiskRegister.query.filter(
            RiskRegister.status.in_(['open', 'monitoring'])
        ).all()
        high_risks = [r for r in risks_open if r.severity == 'High']

        return dict(
            ym=ym, year=year, month=month,
            bookings=bookings, events=events, sessions=sessions,
            meetings=meetings, proposals=proposals, approved=approved,
            milestones_reached=milestones_reached, tasks_done=tasks_done,
            risks_open=risks_open, high_risks=high_risks,
        )

    @app.route('/reports', methods=['GET', 'POST'])
    def reports():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('reports')
            return redirect(url_for('reports'))
        reports_list = MonthlyReport.query.order_by(MonthlyReport.created_at.desc()).all()
        today = date.today()
        stats = _month_stats(today.year, today.month)
        return render_template('reports.html', reports=reports_list, stats=stats,
                               current_month=stats['ym'])

    @app.route('/reports/generate/<int:year>/<int:month>')
    def report_generate(year, month):
        if not login_required():
            return jsonify({'error': 'unauthorized'}), 401
        month = max(1, min(12, month))
        s = _month_stats(year, month)
        month_name = cal_module.month_name[month]

        lines = [f'Monthly Report — {month_name} {year}', '']

        # Research activity
        lines.append('RESEARCH ACTIVITY')
        if s['sessions']:
            proj_names = {}
            for sess in s['sessions']:
                pname = sess.project.title if sess.project else 'Unknown project'
                proj_names.setdefault(pname, []).append(sess)
            for pname, sess_list in proj_names.items():
                lines.append(f'  · {pname}: {len(sess_list)} session{"s" if len(sess_list)!=1 else ""}')
        else:
            lines.append('  · No research sessions logged this month.')
        lines.append('')

        # Space use
        lines.append('SPACE USE')
        if s['bookings']:
            by_type = {}
            for b in s['bookings']:
                by_type.setdefault(b.booking_type, []).append(b)
            for btype, blist in sorted(by_type.items()):
                lines.append(f'  · {btype}: {len(blist)} booking{"s" if len(blist)!=1 else ""}')
        else:
            lines.append('  · No space bookings this month.')
        lines.append('')

        # Program / dissemination
        lines.append('PROGRAM & DISSEMINATION')
        if s['events']:
            for e in s['events']:
                lines.append(f'  · {e.title} ({e.format})')
        else:
            lines.append('  · No dissemination events this month.')
        lines.append('')

        # Governance
        lines.append('GOVERNANCE')
        if s['meetings']:
            for m in s['meetings']:
                lines.append(f'  · {m.title} ({m.meeting_type}, {m.meeting_date})')
        else:
            lines.append('  · No meetings held this month.')
        if s['approved']:
            lines.append(f'  Proposals approved: {len(s["approved"])}')
            for p in s['approved']:
                lines.append(f'    — {p.proposal_text[:80]}{"…" if len(p.proposal_text)>80 else ""}')
        lines.append('')

        # Milestones & tasks
        lines.append('MILESTONES & TASKS')
        if s['milestones_reached']:
            for ms in s['milestones_reached']:
                lines.append(f'  · Milestone reached: {ms.title}')
        if s['tasks_done']:
            lines.append(f'  · Tasks completed: {len(s["tasks_done"])}')
        if not s['milestones_reached'] and not s['tasks_done']:
            lines.append('  · No milestones or tasks completed this month.')
        lines.append('')

        # Risks
        lines.append('RISK REGISTER')
        lines.append(f'  · Open risks: {len(s["risks_open"])} ({len(s["high_risks"])} high severity)')
        if s['high_risks']:
            for r in s['high_risks']:
                lines.append(f'    ⚠ {r.title} — {r.status}')
        lines.append('')

        lines.append('NOTES & OBSERVATIONS')
        lines.append('  [Add any qualitative reflections, unexpected developments, or forward-looking notes here.]')

        return jsonify({'draft': '\n'.join(lines)})

    # ── Working Groups ──

    @app.route('/working-groups', methods=['GET', 'POST'])
    def working_groups():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('working_groups')
            return redirect(url_for('working_groups'))
        return render_template('working_groups.html',
                               wgs=WorkingGroup.query.order_by(WorkingGroup.status, WorkingGroup.name).all(),
                               users=User.query.order_by(User.name).all())

    @app.route('/working-groups/<int:wg_id>/add-member', methods=['POST'])
    def add_wg_member(wg_id):
        if not login_required():
            return redirect(url_for('login'))
        wg = db.session.get(WorkingGroup, wg_id)
        if not wg:
            abort(404)
        user_id = int(request.form.get('user_id', 0))
        role = request.form.get('role', 'member')
        if user_id and not WorkingGroupMembership.query.filter_by(wg_id=wg_id, user_id=user_id).first():
            db.session.add(WorkingGroupMembership(wg_id=wg_id, user_id=user_id, role=role))
            db.session.commit()
            flash('Member added to working group.', 'success')
        return redirect(url_for('record_detail', kind='working_groups', record_id=wg_id))

    @app.route('/working-groups/<int:wg_id>/remove-member/<int:mid>', methods=['POST'])
    def remove_wg_member(wg_id, mid):
        if not login_required() or not is_manager():
            abort(403)
        m = db.session.get(WorkingGroupMembership, mid)
        if m and m.wg_id == wg_id:
            db.session.delete(m)
            db.session.commit()
            flash('Member removed.', 'info')
        return redirect(url_for('record_detail', kind='working_groups', record_id=wg_id))

    # ── Tasks ──

    @app.route('/tasks', methods=['GET', 'POST'])
    def tasks():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            t = Task(
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                status=request.form.get('status', 'todo'),
                priority=request.form.get('priority', 'normal'),
                domain=request.form.get('domain') or None,
                due_date=parse_date(request.form.get('due_date')),
                assigned_to_id=int(request.form['assigned_to_id']) if request.form.get('assigned_to_id') else None,
                entity_type=request.form.get('entity_type') or None,
                entity_id=int(request.form['entity_id']) if request.form.get('entity_id') else None,
                url=request.form.get('url', '').strip(),
                created_by_id=current_user().id,
            )
            db.session.add(t)
            db.session.flush()
            _add_audit_log('tasks', t.id, 'create')
            db.session.commit()
            flash('Task created.', 'success')
            next_url = request.form.get('next') or request.referrer
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('tasks'))
        q = request.args.get('q', '').strip()
        status_f = request.args.get('status', '')
        assignee_f = request.args.get('assignee', '')
        priority_f = request.args.get('priority', '')
        entity_type_f = request.args.get('entity_type', '')
        domain_f = request.args.get('domain', '')
        query = Task.query
        if q:
            query = query.filter(Task.title.ilike(f'%{q}%') | Task.description.ilike(f'%{q}%'))
        if status_f:
            query = query.filter_by(status=status_f)
        if assignee_f:
            query = query.filter_by(assigned_to_id=int(assignee_f))
        if priority_f:
            query = query.filter_by(priority=priority_f)
        if entity_type_f:
            query = query.filter_by(entity_type=entity_type_f)
        if domain_f:
            query = query.filter_by(domain=domain_f)
        # Build entity lookup maps for display
        entity_maps = {
            'projects': {p.id: p.title for p in ResearchProject.query.all()},
            'events': {e.id: e.title for e in DisseminationEvent.query.all()},
            'working_groups': {wg.id: wg.name for wg in WorkingGroup.query.all()},
            'governance': {m.id: m.title for m in Meeting.query.all()},
            'partnerships': {p.id: p.institution.name if p.institution else f'Partnership #{p.id}' for p in Partnership.query.all()},
        }
        return render_template('tasks.html',
                               tasks=query.order_by(Task.due_date.asc(), Task.priority.desc()).all(),
                               users=User.query.order_by(User.name).all(),
                               projects=ResearchProject.query.order_by(ResearchProject.title).all(),
                               events=DisseminationEvent.query.order_by(DisseminationEvent.event_date.desc()).all(),
                               working_groups=WorkingGroup.query.order_by(WorkingGroup.name).all(),
                               meetings=Meeting.query.order_by(Meeting.meeting_date.desc()).limit(20).all(),
                               partnerships=Partnership.query.join(Institution).order_by(Institution.name).all(),
                               entity_maps=entity_maps,
                               q=q, status_f=status_f, assignee_f=assignee_f,
                               priority_f=priority_f, entity_type_f=entity_type_f,
                               domain_f=domain_f, now=date.today())

    @app.route('/tasks/<int:task_id>/status', methods=['POST'])
    def update_task_status(task_id):
        if not login_required():
            return redirect(url_for('login'))
        t = db.session.get(Task, task_id)
        if t:
            t.status = request.form.get('status', t.status)
            db.session.commit()
        return redirect(request.referrer or url_for('tasks'))

    # ── Constitution ──

    @app.route('/constitution', methods=['GET', 'POST'])
    def constitution():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('constitution')
            return redirect(url_for('constitution'))
        docs = ConstitutionDocument.query.order_by(ConstitutionDocument.category, ConstitutionDocument.title).all()
        protocol_rules = ProtocolRule.query.all()
        policies = PolicyDocument.query.all()
        risks = RiskRegister.query.filter(RiskRegister.status != 'closed').all()
        return render_template('constitution.html', docs=docs,
                               protocol_rules=protocol_rules, policies=policies, risks=risks)

    # ── Polls ──

    @app.route('/polls', methods=['GET', 'POST'])
    def polls():
        if not login_required():
            return redirect(url_for('login'))
        return render_template('polls.html',
                               polls=Poll.query.order_by(Poll.id.desc()).all())

    @app.route('/polls/new', methods=['GET', 'POST'])
    def polls_new():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            is_pub = 'is_public' in request.form
            pub_token = uuid.uuid4().hex if is_pub else None
            poll = Poll(
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                poll_type=request.form.get('poll_type', 'single'),
                status='open',
                deadline=parse_dt(request.form.get('deadline')) if request.form.get('deadline') else None,
                is_public=is_pub,
                public_token=pub_token,
                created_by_id=current_user().id,
            )
            db.session.add(poll)
            db.session.flush()
            # Options
            for i, opt_text in enumerate(request.form.getlist('option_text')):
                if opt_text.strip():
                    db.session.add(PollOption(poll_id=poll.id, option_text=opt_text.strip(), order=i))
            _add_audit_log('polls', poll.id, 'create')
            db.session.commit()
            flash('Poll created.', 'success')
            return redirect(url_for('poll_detail', poll_id=poll.id))
        return render_template('poll_new.html')

    @app.route('/polls/<int:poll_id>', methods=['GET', 'POST'])
    def poll_detail(poll_id):
        if not login_required():
            return redirect(url_for('login'))
        poll = db.session.get(Poll, poll_id)
        if not poll:
            abort(404)
        user = current_user()
        user_voted = PollVote.query.filter_by(poll_id=poll_id, user_id=user.id).first() is not None if user else False
        if request.method == 'POST' and poll.status == 'open' and not user_voted:
            option_ids = request.form.getlist('option_id')
            if poll.poll_type == 'single' and option_ids:
                option_ids = [option_ids[0]]
            for oid in option_ids:
                db.session.add(PollVote(poll_id=poll_id, option_id=int(oid), user_id=user.id))
            db.session.commit()
            flash('Vote recorded.', 'success')
            return redirect(url_for('poll_detail', poll_id=poll_id))
        options = poll.options.all()
        vote_counts = {}
        total_votes = 0
        for opt in options:
            count = PollVote.query.filter_by(poll_id=poll_id, option_id=opt.id).count()
            vote_counts[opt.id] = count
            total_votes += count
        tokens = PollToken.query.filter_by(poll_id=poll_id).order_by(PollToken.created_at.desc()).all()
        return render_template('poll_detail.html', poll=poll, options=options,
                               vote_counts=vote_counts, total_votes=total_votes,
                               user_voted=user_voted, tokens=tokens)

    @app.route('/polls/<int:poll_id>/toggle-status', methods=['POST'])
    def toggle_poll_status(poll_id):
        if not login_required() or not is_manager():
            abort(403)
        poll = db.session.get(Poll, poll_id)
        if poll:
            poll.status = 'closed' if poll.status == 'open' else 'open'
            db.session.commit()
            flash(f"Poll {'closed' if poll.status == 'closed' else 're-opened'}.", 'info')
        return redirect(url_for('poll_detail', poll_id=poll_id))

    @app.route('/polls/<int:poll_id>/tokens', methods=['POST'])
    def generate_poll_token(poll_id):
        if not login_required() or not is_manager():
            abort(403)
        poll = db.session.get(Poll, poll_id)
        if not poll:
            abort(404)
        label = request.form.get('label', '').strip()
        count = int(request.form.get('count', 1))
        for _ in range(min(count, 50)):
            db.session.add(PollToken(
                poll_id=poll_id,
                token=uuid.uuid4().hex,
                label=label
            ))
        db.session.commit()
        flash(f'{count} invite token(s) generated.', 'success')
        return redirect(url_for('poll_detail', poll_id=poll_id))

    @app.route('/vote/<token>', methods=['GET', 'POST'])
    def public_vote(token):
        # Try public token first
        poll = Poll.query.filter_by(public_token=token).first()
        poll_token = None
        if not poll:
            poll_token = PollToken.query.filter_by(token=token).first()
            if poll_token:
                poll = db.session.get(Poll, poll_token.poll_id)
        if not poll:
            abort(404)
        if poll.status != 'open':
            return render_template('vote_public.html', poll=poll, closed=True, options=[], vote_counts={}, total_votes=0)
        if poll_token and poll_token.used:
            return render_template('vote_public.html', poll=poll, already_voted=True, options=[], vote_counts={}, total_votes=0)
        # Check session for public token voting
        session_key = f'voted_poll_{poll.id}'
        already_voted = session.get(session_key, False)
        if request.method == 'POST' and not already_voted:
            option_ids = request.form.getlist('option_id')
            if poll.poll_type == 'single' and option_ids:
                option_ids = [option_ids[0]]
            anon = uuid.uuid4().hex
            for oid in option_ids:
                db.session.add(PollVote(poll_id=poll.id, option_id=int(oid), anon_token=anon))
            if poll_token:
                poll_token.used = True
                poll_token.used_at = datetime.utcnow()
            db.session.commit()
            session[session_key] = True
            flash('Your vote has been recorded. Thank you.', 'success')
            return redirect(url_for('public_vote', token=token))
        options = poll.options.all()
        vote_counts = {}
        total_votes = 0
        for opt in options:
            count = PollVote.query.filter_by(poll_id=poll.id, option_id=opt.id).count()
            vote_counts[opt.id] = count
            total_votes += count
        return render_template('vote_public.html', poll=poll, options=options,
                               vote_counts=vote_counts, total_votes=total_votes,
                               already_voted=already_voted,
                               poll_token=poll_token, closed=False)

    # ── Audit ──

    @app.route('/audit')
    def audit():
        if not login_required():
            return redirect(url_for('login'))
        if not is_manager():
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        q = request.args.get('q', '').strip()
        entity_type = request.args.get('entity_type', '')
        query = AuditLog.query
        if q:
            query = query.filter(AuditLog.entity_type.ilike(f'%{q}%') | AuditLog.field_changed.ilike(f'%{q}%'))
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        entries = query.order_by(AuditLog.timestamp.desc()).limit(200).all()
        entity_types = [r[0] for r in db.session.query(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type).all()]
        return render_template('audit.html', entries=entries, q=q, entity_type=entity_type, entity_types=entity_types)

    # ── Research Journal (all sessions) ──

    @app.route('/journal')
    def journal():
        if not login_required():
            return redirect(url_for('login'))
        project_id = request.args.get('project', '')
        q = request.args.get('q', '').strip()
        query = ResearchSession.query
        if project_id:
            query = query.filter_by(project_id=int(project_id))
        if q:
            query = query.filter(
                ResearchSession.observations.ilike(f'%{q}%') |
                ResearchSession.methods_used.ilike(f'%{q}%') |
                ResearchSession.open_questions.ilike(f'%{q}%') |
                ResearchSession.facilitator.ilike(f'%{q}%') |
                ResearchSession.participants.ilike(f'%{q}%')
            )
        sessions_list = query.order_by(ResearchSession.session_date.desc()).all()
        projects = ResearchProject.query.order_by(ResearchProject.title).all()
        project_map = {p.id: p for p in projects}
        return render_template('journal.html', sessions=sessions_list, projects=projects,
                               project_map=project_map, project_filter=project_id, q=q)

    # ── Sub-entity create routes ──

    @app.route('/sessions', methods=['POST'])
    def sessions():
        if not login_required():
            return redirect(url_for('login'))
        try:
            project_id = int(request.form['project_id'])
        except (ValueError, KeyError):
            flash('Invalid project.', 'danger')
            return redirect(url_for('projects'))
        sess = ResearchSession(
            project_id=project_id,
            session_date=parse_date(request.form.get('session_date')) or date.today(),
            facilitator=request.form.get('facilitator', ''),
            participants=request.form.get('participants', ''),
            methods_used=request.form.get('methods_used', ''),
            observations=request.form.get('observations', ''),
            open_questions=request.form.get('open_questions', ''),
            created_by_id=current_user().id,
        )
        db.session.add(sess)
        db.session.flush()
        _add_audit_log('sessions', sess.id, 'create')
        db.session.commit()
        flash('Research session logged.', 'success')
        return redirect(url_for('record_detail', kind='projects', record_id=project_id))

    @app.route('/proposals', methods=['POST'])
    def proposals():
        if not login_required():
            return redirect(url_for('login'))
        try:
            meeting_id = int(request.form['meeting_id'])
        except (ValueError, KeyError):
            flash('Invalid meeting.', 'danger')
            return redirect(url_for('governance'))
        prop = ProposalRecord(
            meeting_id=meeting_id,
            proposal_text=request.form.get('proposal_text', ''),
            proposer=request.form.get('proposer', ''),
            outcome=request.form.get('outcome', 'pending'),
            votes_for=int(request.form.get('votes_for', 0) or 0),
            votes_against=int(request.form.get('votes_against', 0) or 0),
            dissenting_notes=request.form.get('dissenting_notes', ''),
            created_by_id=current_user().id,
        )
        db.session.add(prop)
        db.session.flush()
        _add_audit_log('proposals', prop.id, 'create')
        db.session.commit()
        flash('Proposal recorded.', 'success')
        return redirect(url_for('record_detail', kind='governance', record_id=meeting_id))

    # ── File Attachments ──

    @app.route('/records/<kind>/<int:record_id>/upload', methods=['POST'])
    def upload_attachment(kind, record_id):
        if not login_required():
            return redirect(url_for('login'))
        config = RECORD_CONFIG.get(kind)
        if not config:
            abort(404)
        obj = db.session.get(config['model'], record_id)
        if not obj:
            abort(404)
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected.', 'warning')
            return redirect(url_for('record_detail', kind=kind, record_id=record_id))
        f = request.files['file']
        original = secure_filename(f.filename)
        ext = os.path.splitext(original)[1]
        stored_name = uuid.uuid4().hex + ext
        upload_dir = os.path.join(app.instance_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        f.save(os.path.join(upload_dir, stored_name))
        att = Attachment(
            entity_type=kind, entity_id=record_id,
            filename=stored_name, original_name=original,
            uploaded_by_id=current_user().id,
        )
        db.session.add(att)
        db.session.commit()
        flash('File uploaded.', 'success')
        return redirect(url_for('record_detail', kind=kind, record_id=record_id))

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        if not login_required():
            return redirect(url_for('login'))
        upload_dir = os.path.join(app.instance_path, 'uploads')
        return send_from_directory(upload_dir, filename)

    # ── Generic record detail ──

    @app.route('/records/<kind>/<int:record_id>', methods=['GET', 'POST'])
    def record_detail(kind, record_id):
        if not login_required():
            return redirect(url_for('login'))
        config = RECORD_CONFIG.get(kind)
        if not config:
            abort(404)
        obj = db.session.get(config['model'], record_id)
        if not obj:
            abort(404)
        if request.method == 'POST':
            if not can_edit_record(obj):
                flash('You do not have permission to edit this item.', 'danger')
                return redirect(url_for('record_detail', kind=kind, record_id=record_id))
            original_project_id = getattr(obj, 'project_id', None)
            old_vals = _capture_values(obj, config)
            apply_form_to_record(obj, config)
            new_vals = _capture_values(obj, config)
            if kind == 'bookings':
                conflict = Booking.query.filter(
                    Booking.space == obj.space, Booking.id != obj.id,
                    Booking.start_dt < obj.end_dt, Booking.end_dt > obj.start_dt
                ).first()
                if conflict:
                    obj.project_id = original_project_id
                    db.session.rollback()
                    flash(f'Conflict with booking #{conflict.id} in {obj.space}.', 'danger')
                    return redirect(url_for('record_detail', kind=kind, record_id=record_id))
            _log_field_changes(kind, obj.id, old_vals, new_vals)
            db.session.commit()
            flash(f"{config['singular']} updated.", 'success')
            return redirect(url_for('record_detail', kind=kind, record_id=record_id))

        display_fields = []
        for field in config['fields']:
            val = getattr(obj, field['name'], '') if field['name'] != 'password' else ''
            if val is None:
                val = ''
            if field['name'] == 'project_id' and getattr(obj, 'project', None):
                display = obj.project.title
            elif field['name'] == 'institution_id' and getattr(obj, 'institution', None):
                display = obj.institution.name
            elif field['name'] == 'meeting_id' and getattr(obj, 'meeting', None):
                display = f"{obj.meeting.meeting_date} · {obj.meeting.title}"
            elif field['name'] == 'facility_id' and getattr(obj, 'facility', None):
                display = obj.facility.name
            elif field['name'] == 'assigned_to_id' and getattr(obj, 'assignee', None):
                display = obj.assignee.name
            elif field['name'] == 'working_group_id' and getattr(obj, 'working_group', None):
                display = obj.working_group.name
            elif field.get('type') == 'checkbox':
                display = 'Yes' if val else 'No'
            else:
                display = val
            display_fields.append({
                'field': field,
                'display': display,
                'value': format_value(val, field.get('type', 'text')),
                'options': field.get('choices') or field.get('options_provider', lambda _: [])(field['name'])
            })

        creator = db.session.get(User, getattr(obj, 'created_by_id', None)) if hasattr(obj, 'created_by_id') else None
        rs_sessions = ResearchSession.query.filter_by(project_id=obj.id).order_by(ResearchSession.session_date.desc()).all() if kind == 'projects' else []
        project_members = ProjectMembership.query.filter_by(project_id=obj.id).all() if kind == 'projects' else []
        project_milestones = Milestone.query.filter_by(project_id=obj.id).order_by(Milestone.target_date).all() if kind == 'projects' else []
        project_tasks = Task.query.filter_by(entity_type='projects', entity_id=obj.id).order_by(Task.due_date).all() if kind == 'projects' else []
        entity_tasks = Task.query.filter_by(entity_type=kind, entity_id=obj.id).order_by(Task.due_date).all() if kind not in ('projects',) else []
        project_budget_items = BudgetItem.query.filter_by(project_id=obj.id).order_by(BudgetItem.item_date.desc()).all() if kind == 'projects' else []
        project_bookings = Booking.query.filter_by(project_id=obj.id).order_by(Booking.start_dt.desc()).limit(6).all() if kind == 'projects' else []
        project_events = DisseminationEvent.query.filter_by(project_id=obj.id).order_by(DisseminationEvent.event_date.desc()).all() if kind == 'projects' else []
        meeting_proposals = ProposalRecord.query.filter_by(meeting_id=obj.id).order_by(ProposalRecord.id).all() if kind == 'governance' else []
        facility_equipment = Equipment.query.filter_by(facility_id=obj.id).all() if kind == 'facilities' else []
        wg_memberships = WorkingGroupMembership.query.filter_by(wg_id=obj.id).all() if kind == 'working_groups' else []
        wg_meetings = Meeting.query.filter_by(working_group_id=obj.id).order_by(Meeting.meeting_date.desc()).all() if kind == 'working_groups' else []
        attachments = Attachment.query.filter_by(entity_type=kind, entity_id=obj.id).order_by(Attachment.uploaded_at.desc()).all()
        audit_entries = AuditLog.query.filter_by(entity_type=kind, entity_id=obj.id).order_by(AuditLog.timestamp.desc()).limit(30).all()
        all_users = User.query.order_by(User.name).all()

        # Budget summary for projects
        project_budget_summary = None
        if kind == 'projects':
            proj_income = sum(i.amount for i in project_budget_items if i.direction == 'income')
            proj_expense = sum(i.amount for i in project_budget_items if i.direction == 'expense')
            project_budget_summary = {'income': proj_income, 'expense': proj_expense, 'net': proj_income - proj_expense, 'allocation': obj.budget_allocation or 0}

        return render_template('record_detail.html',
                               kind=kind, config=config, obj=obj, display_fields=display_fields, creator=creator,
                               can_edit=can_edit_record(obj), is_manager=is_manager(),
                               rs_sessions=rs_sessions, meeting_proposals=meeting_proposals,
                               project_members=project_members, project_milestones=project_milestones,
                               project_tasks=project_tasks, project_budget_items=project_budget_items,
                               project_budget_summary=project_budget_summary,
                               facility_equipment=facility_equipment, wg_memberships=wg_memberships,
                               wg_meetings=wg_meetings,
                               project_bookings=project_bookings,
                               project_events=project_events,
                               attachments=attachments, audit_entries=audit_entries,
                               all_users=all_users, now_date=date.today(),
                               entity_tasks=entity_tasks)

    # ── Legacy Planning Dashboard ──

    @app.route('/legacy', methods=['GET', 'POST'])
    def legacy():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('legacy_tasks')
            db.session.commit()
            flash('Legacy task created.', 'success')
            return redirect(url_for('legacy'))
        category_filter = request.args.get('category', '')
        status_filter = request.args.get('status', '')
        query = LegacyTask.query
        if category_filter:
            query = query.filter_by(category=category_filter)
        if status_filter:
            query = query.filter_by(status=status_filter)
        tasks = query.order_by(LegacyTask.deadline, LegacyTask.priority).all()
        today = date.today()
        # Summary stats
        all_tasks = LegacyTask.query.all()
        total = len(all_tasks)
        done_count = sum(1 for t in all_tasks if t.status == 'done')
        overdue_count = sum(1 for t in all_tasks if t.deadline and t.deadline < today and t.status != 'done')
        blocked_count = sum(1 for t in all_tasks if t.status == 'blocked')
        # Equipment without transfer plan
        equipment_no_plan = Equipment.query.filter(
            (Equipment.transfer_plan == '') | (Equipment.transfer_plan == None)
        ).filter_by(status='available').count()
        # Projects without outputs
        projects_no_output = ResearchProject.query.filter(
            (ResearchProject.outputs == '') | (ResearchProject.outputs == None)
        ).filter_by(status='active').count()
        categories = ['equipment', 'knowledge', 'partnership', 'funding', 'governance', 'research']
        by_category = {}
        for cat in categories:
            cat_tasks = [t for t in all_tasks if t.category == cat]
            done = sum(1 for t in cat_tasks if t.status == 'done')
            by_category[cat] = {'total': len(cat_tasks), 'done': done}
        return render_template('legacy.html', tasks=tasks, today=today,
                               total=total, done_count=done_count,
                               overdue_count=overdue_count, blocked_count=blocked_count,
                               equipment_no_plan=equipment_no_plan,
                               projects_no_output=projects_no_output,
                               by_category=by_category, categories=categories,
                               category_filter=category_filter, status_filter=status_filter)

    # ── Legacy task quick status update ──

    @app.route('/legacy/<int:task_id>/status', methods=['POST'])
    def legacy_task_status(task_id):
        if not login_required():
            return redirect(url_for('login'))
        task = db.session.get(LegacyTask, task_id)
        if not task:
            abort(404)
        new_status = request.form.get('status', task.status)
        old_status = task.status
        task.status = new_status
        _add_audit_log('legacy_tasks', task.id, 'update', 'status', old_status, new_status)
        db.session.commit()
        flash(f'"{task.title}" marked as {new_status}.', 'success')
        return redirect(url_for('legacy'))

    # ── Org Health Check ──

    @app.route('/health')
    def health():
        if not login_required():
            return redirect(url_for('login'))
        today = date.today()

        # Stale projects (active, no session in 30+ days, or never)
        all_active_projects = ResearchProject.query.filter_by(status='active').all()
        stale_projects = []
        for p in all_active_projects:
            last = ResearchSession.query.filter_by(project_id=p.id).order_by(ResearchSession.session_date.desc()).first()
            if last is None:
                stale_projects.append({'project': p, 'days': None, 'issue': 'no sessions logged'})
            elif (today - last.session_date).days > 30:
                stale_projects.append({'project': p, 'days': (today - last.session_date).days, 'issue': f'{(today - last.session_date).days} days since last session'})

        # Projects with no outputs
        projects_no_output = [p for p in all_active_projects if not (p.outputs or '').strip()]

        # Overdue tasks
        overdue_tasks = Task.query.filter(
            Task.due_date < today, Task.status.notin_(['done'])
        ).order_by(Task.due_date.asc()).limit(10).all()

        # High/urgent open risks
        high_risks = RiskRegister.query.filter(
            RiskRegister.status != 'closed',
            RiskRegister.severity.in_(['High', 'Critical'])
        ).all()

        # Milestones missed or overdue
        overdue_milestones = Milestone.query.filter(
            Milestone.target_date < today,
            Milestone.status == 'pending'
        ).order_by(Milestone.target_date.asc()).limit(10).all()

        # Urgent legacy tasks overdue
        overdue_legacy = LegacyTask.query.filter(
            LegacyTask.deadline < today,
            LegacyTask.status.notin_(['done'])
        ).order_by(LegacyTask.deadline.asc()).all()

        # Equipment without transfer plan
        equipment_no_plan = Equipment.query.filter(
            (Equipment.transfer_plan == '') | (Equipment.transfer_plan == None)
        ).filter(Equipment.status != 'decommissioned').all()

        # Blocked items
        blocked_tasks = LegacyTask.query.filter_by(status='blocked').all()
        blocked_tasks_all = Task.query.filter_by(status='blocked').all()

        # Upcoming deadlines in next 30 days (legacy + milestones)
        future_date = date(today.year + (today.month // 12), (today.month % 12) + 1, today.day) if today.month < 12 else date(today.year + 1, 1, today.day)
        upcoming_deadlines = []
        for lt in LegacyTask.query.filter(
            LegacyTask.deadline >= today,
            LegacyTask.deadline <= future_date,
            LegacyTask.status.notin_(['done'])
        ).order_by(LegacyTask.deadline.asc()).limit(10).all():
            upcoming_deadlines.append({'label': lt.title, 'date': lt.deadline, 'kind': 'legacy', 'url': url_for('record_detail', kind='legacy_tasks', record_id=lt.id)})
        for ms in Milestone.query.filter(
            Milestone.target_date >= today,
            Milestone.target_date <= future_date,
            Milestone.status == 'pending'
        ).order_by(Milestone.target_date.asc()).limit(10).all():
            upcoming_deadlines.append({'label': ms.title, 'date': ms.target_date, 'kind': 'milestone', 'url': url_for('record_detail', kind='milestones', record_id=ms.id)})
        upcoming_deadlines.sort(key=lambda x: x['date'])

        # Score the health (simple points system)
        issues = (len(stale_projects) + len(overdue_tasks) + len(high_risks) +
                  len(overdue_milestones) + len(overdue_legacy) + len(blocked_tasks))
        if issues == 0:
            health_label = 'Good'
            health_color = '#5c7c5c'
        elif issues <= 3:
            health_label = 'Attention needed'
            health_color = '#ffc107'
        elif issues <= 8:
            health_label = 'Several issues'
            health_color = '#fd7e14'
        else:
            health_label = 'Critical'
            health_color = '#dc3545'

        return render_template('health.html', today=today,
                               stale_projects=stale_projects,
                               projects_no_output=projects_no_output,
                               overdue_tasks=overdue_tasks,
                               high_risks=high_risks,
                               overdue_milestones=overdue_milestones,
                               overdue_legacy=overdue_legacy,
                               equipment_no_plan=equipment_no_plan,
                               blocked_tasks=blocked_tasks,
                               blocked_tasks_all=blocked_tasks_all,
                               upcoming_deadlines=upcoming_deadlines,
                               health_label=health_label,
                               health_color=health_color,
                               issues=issues)

    # ── Print views ──

    @app.route('/records/governance/<int:record_id>/print')
    def print_meeting(record_id):
        if not login_required():
            return redirect(url_for('login'))
        m = db.session.get(Meeting, record_id)
        if not m:
            abort(404)
        proposals = ProposalRecord.query.filter_by(meeting_id=m.id).order_by(ProposalRecord.id).all()
        return render_template('print_meeting.html', m=m, proposals=proposals, today=date.today())

    @app.route('/records/projects/<int:record_id>/print')
    def print_project(record_id):
        if not login_required():
            return redirect(url_for('login'))
        p = db.session.get(ResearchProject, record_id)
        if not p:
            abort(404)
        sessions = ResearchSession.query.filter_by(project_id=p.id).order_by(ResearchSession.session_date.desc()).all()
        milestones = Milestone.query.filter_by(project_id=p.id).order_by(Milestone.target_date).all()
        members = ProjectMembership.query.filter_by(project_id=p.id).all()
        return render_template('print_project.html', p=p, sessions=sessions, milestones=milestones, members=members, today=date.today())

    @app.route('/records/reports/<int:record_id>/print')
    def print_report(record_id):
        if not login_required():
            return redirect(url_for('login'))
        report = db.session.get(MonthlyReport, record_id)
        if not report:
            abort(404)
        creator = db.session.get(User, report.created_by_id) if report.created_by_id else None
        return render_template('print_report.html', report=report, creator=creator)

    # ── Global Search ──

    @app.route('/search')
    def search():
        if not login_required():
            return redirect(url_for('login'))
        q = request.args.get('q', '').strip()
        if not q or len(q) < 2:
            return render_template('search.html', q=q, results={}, total=0)
        like = f'%{q}%'
        results = {}

        projects = ResearchProject.query.filter(
            ResearchProject.title.ilike(like) |
            ResearchProject.lead.ilike(like) |
            ResearchProject.research_question.ilike(like) |
            ResearchProject.outputs.ilike(like)
        ).limit(10).all()
        if projects:
            results['projects'] = [{'label': p.title, 'sub': f'{p.phase} · {p.lead}', 'url': url_for('record_detail', kind='projects', record_id=p.id)} for p in projects]

        sessions = ResearchSession.query.filter(
            ResearchSession.observations.ilike(like) |
            ResearchSession.methods_used.ilike(like) |
            ResearchSession.open_questions.ilike(like) |
            ResearchSession.facilitator.ilike(like)
        ).limit(10).all()
        if sessions:
            results['sessions'] = [{'label': f'Session {s.session_date}', 'sub': s.facilitator + (' · ' + s.observations[:60] if s.observations else ''), 'url': url_for('record_detail', kind='sessions', record_id=s.id)} for s in sessions]

        meetings = Meeting.query.filter(
            Meeting.title.ilike(like) |
            Meeting.body.ilike(like) |
            Meeting.decisions.ilike(like)
        ).limit(10).all()
        if meetings:
            results['meetings'] = [{'label': m.title, 'sub': str(m.meeting_date) + ' · ' + m.meeting_type, 'url': url_for('record_detail', kind='governance', record_id=m.id)} for m in meetings]

        risks = RiskRegister.query.filter(
            RiskRegister.title.ilike(like) |
            RiskRegister.mitigation.ilike(like) |
            RiskRegister.owner.ilike(like)
        ).limit(8).all()
        if risks:
            results['risks'] = [{'label': r.title, 'sub': f'{r.severity} · {r.owner}', 'url': url_for('record_detail', kind='risks', record_id=r.id)} for r in risks]

        equipment = Equipment.query.filter(
            Equipment.name.ilike(like) |
            Equipment.category.ilike(like) |
            Equipment.owner.ilike(like)
        ).limit(8).all()
        if equipment:
            results['equipment'] = [{'label': e.name, 'sub': f'{e.category} · {e.status}', 'url': url_for('record_detail', kind='equipment', record_id=e.id)} for e in equipment]

        policies = PolicyDocument.query.filter(
            PolicyDocument.title.ilike(like) |
            PolicyDocument.content.ilike(like) |
            PolicyDocument.category.ilike(like)
        ).limit(8).all()
        if policies:
            results['policies'] = [{'label': p.title, 'sub': f'{p.category} v{p.version}', 'url': url_for('record_detail', kind='policies', record_id=p.id)} for p in policies]

        events = DisseminationEvent.query.filter(
            DisseminationEvent.title.ilike(like) |
            DisseminationEvent.format.ilike(like) |
            DisseminationEvent.notes.ilike(like)
        ).limit(8).all()
        if events:
            results['events'] = [{'label': e.title, 'sub': f'{e.event_date} · {e.format}', 'url': url_for('record_detail', kind='events', record_id=e.id)} for e in events]

        institutions = Institution.query.filter(
            Institution.name.ilike(like) |
            Institution.notes.ilike(like)
        ).limit(8).all()
        if institutions:
            results['institutions'] = [{'label': i.name, 'sub': i.category, 'url': url_for('record_detail', kind='institutions', record_id=i.id)} for i in institutions]

        total = sum(len(v) for v in results.values())
        return render_template('search.html', q=q, results=results, total=total)

    # ── About ──

    @app.route('/about')
    def about():
        if not login_required():
            return redirect(url_for('login'))
        live_stats = {
            'active_projects': ResearchProject.query.filter_by(status='active').count(),
            'research_sessions': ResearchSession.query.count(),
            'total_sessions_observations': ResearchSession.query.filter(ResearchSession.observations != '').count(),
            'total_meetings': Meeting.query.count(),
            'approved_proposals': ProposalRecord.query.filter_by(outcome='approved').count(),
            'rejected_proposals': ProposalRecord.query.filter_by(outcome='rejected').count(),
            'active_partnerships': Partnership.query.filter_by(status='active').count(),
            'equipment_items': Equipment.query.count(),
            'equipment_with_plan': Equipment.query.filter(Equipment.transfer_plan != '').count(),
            'total_budget_income': db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='income').scalar(),
            'total_budget_expense': db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='expense').scalar(),
            'open_risks': RiskRegister.query.filter(RiskRegister.status != 'closed').count(),
            'legacy_done': LegacyTask.query.filter_by(status='done').count(),
            'legacy_total': LegacyTask.query.count(),
            'protocol_rules': ProtocolRule.query.count(),
            'policy_docs': PolicyDocument.query.count(),
        }
        return render_template('about.html', live_stats=live_stats)
