from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
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
    AuditLog, ResearchSession, ProposalRecord, Attachment
)


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
            {'name': 'phase', 'label': 'Phase', 'type': 'select', 'choices': [('phase_i', 'Phase I'), ('phase_ii', 'Phase II'), ('pilot', 'Pilot')]},
            {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('active', 'active'), ('planned', 'planned'), ('completed', 'completed')]},
            {'name': 'research_question', 'label': 'Research question', 'type': 'textarea'},
            {'name': 'methods', 'label': 'Methods', 'type': 'textarea'},
            {'name': 'outputs', 'label': 'Outputs', 'type': 'textarea'},
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
            {'name': 'owner', 'label': 'Owner'}, {'name': 'transfer_plan', 'label': 'Transfer plan', 'type': 'textarea'},
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
            {'name': 'title', 'label': 'Title'}, {'name': 'meeting_date', 'label': 'Meeting date', 'type': 'date'},
            {'name': 'meeting_type', 'label': 'Meeting type', 'type': 'select', 'choices': [('steering', 'steering'), ('operations', 'operations'), ('working_group', 'working_group')]},
            {'name': 'body', 'label': 'Body', 'type': 'textarea'}, {'name': 'decisions', 'label': 'Decisions', 'type': 'textarea'},
        ],
    },
    'institutions': {
        'model': Institution,
        'title': 'Institutions',
        'singular': 'Institution',
        'list_endpoint': 'partnerships',
        'summary': lambda o: o.name,
        'fields': [
            {'name': 'name', 'label': 'Name'}, {'name': 'category', 'label': 'Category'}, {'name': 'contact_person', 'label': 'Contact person'}, {'name': 'contact_email', 'label': 'Contact email', 'type': 'email'}, {'name': 'notes', 'label': 'Notes', 'type': 'textarea'},
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
            {'name': 'objective', 'label': 'Objective', 'type': 'textarea'}, {'name': 'requested_support', 'label': 'Requested support', 'type': 'textarea'}, {'name': 'timeline', 'label': 'Timeline'},
        ],
    },
    'protocol': {
        'model': ProtocolRule,
        'title': 'Protocol',
        'singular': 'Protocol rule',
        'list_endpoint': 'protocol',
        'summary': lambda o: o.principle,
        'fields': [
            {'name': 'principle', 'label': 'Principle'}, {'name': 'description', 'label': 'Description', 'type': 'textarea'}, {'name': 'implementation', 'label': 'Implementation', 'type': 'textarea'},
        ],
    },
    'policies': {
        'model': PolicyDocument,
        'title': 'Policies',
        'singular': 'Policy document',
        'list_endpoint': 'policies',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'}, {'name': 'category', 'label': 'Category'}, {'name': 'version', 'label': 'Version'}, {'name': 'content', 'label': 'Content', 'type': 'textarea'},
        ],
    },
    'risks': {
        'model': RiskRegister,
        'title': 'Risks',
        'singular': 'Risk',
        'list_endpoint': 'risks',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'}, {'name': 'severity', 'label': 'Severity', 'type': 'select', 'choices': [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]}, {'name': 'owner', 'label': 'Owner'}, {'name': 'mitigation', 'label': 'Mitigation', 'type': 'textarea'}, {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('open', 'open'), ('monitoring', 'monitoring'), ('closed', 'closed')]},
        ],
    },
    'roadmap': {
        'model': RoadmapItem,
        'title': 'Roadmap',
        'singular': 'Roadmap item',
        'list_endpoint': 'roadmap',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'phase', 'label': 'Phase', 'type': 'select', 'choices': [('phase_i', 'Phase I'), ('phase_ii', 'Phase II')]}, {'name': 'title', 'label': 'Title'}, {'name': 'year', 'label': 'Year', 'type': 'int'}, {'name': 'owner', 'label': 'Owner'}, {'name': 'status', 'label': 'Status', 'type': 'select', 'choices': [('planned', 'planned'), ('in_progress', 'in_progress'), ('completed', 'completed')]}, {'name': 'details', 'label': 'Details', 'type': 'textarea'},
        ],
    },
    'events': {
        'model': DisseminationEvent,
        'title': 'Events',
        'singular': 'Dissemination event',
        'list_endpoint': 'events',
        'summary': lambda o: o.title,
        'fields': [
            {'name': 'title', 'label': 'Title'}, {'name': 'event_date', 'label': 'Event date', 'type': 'date'}, {'name': 'format', 'label': 'Format'}, {'name': 'audience', 'label': 'Audience'}, {'name': 'linked_project', 'label': 'Linked project'}, {'name': 'notes', 'label': 'Notes', 'type': 'textarea'},
        ],
    },
    'reports': {
        'model': MonthlyReport,
        'title': 'Reports',
        'singular': 'Monthly report',
        'list_endpoint': 'reports',
        'summary': lambda o: o.month,
        'fields': [
            {'name': 'month', 'label': 'Month'}, {'name': 'summary', 'label': 'Summary', 'type': 'textarea'},
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
    db.session.add(obj)
    db.session.flush()
    _add_audit_log(kind, obj.id, 'create')
    db.session.commit()
    flash(f"{config['singular']} created.", 'success')
    return True


def register_routes(app):
    @app.context_processor
    def inject_user():
        return {'current_user': current_user(), 'can_edit_record': can_edit_record}

    @app.route('/')
    def index():
        if not login_required():
            return redirect(url_for('login'))
        income = db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='income').scalar()
        expense = db.session.query(func.coalesce(func.sum(BudgetItem.amount), 0)).filter_by(direction='expense').scalar()
        stats = {
            'projects': ResearchProject.query.count(),
            'bookings': Booking.query.count(),
            'equipment': Equipment.query.count(),
            'partners': Partnership.query.count(),
            'net_budget': round(income - expense, 2),
            'phase_ii_actions': RoadmapItem.query.filter_by(phase='phase_ii').count(),
        }
        upcoming = Booking.query.order_by(Booking.start_dt.asc()).limit(8).all()
        meetings = Meeting.query.order_by(Meeting.meeting_date.desc()).limit(5).all()
        risks = RiskRegister.query.filter(RiskRegister.status != 'closed').limit(5).all()
        return render_template('dashboard.html', stats=stats, upcoming=upcoming, meetings=meetings, risks=risks)

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
        return render_template('projects.html',
            projects=query.order_by(ResearchProject.start_date.desc()).all(),
            q=q, status=status, phase=phase)

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
        month_bookings = Booking.query.filter(
            Booking.start_dt >= start,
            Booking.start_dt < end
        ).all()
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
            weeks=weeks, day_bookings=day_bookings,
            year=year, month=month, month_name=month_name,
            prev_year=prev_year, prev_month=prev_month,
            next_year=next_year, next_month=next_month,
            today=today, total_bookings=len(month_bookings))

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
            query = query.filter(
                Equipment.name.ilike(f'%{q}%') |
                Equipment.owner.ilike(f'%{q}%')
            )
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        categories = [r[0] for r in db.session.query(Equipment.category).distinct().order_by(Equipment.category).all()]
        return render_template('equipment.html',
            equipment=query.order_by(Equipment.category, Equipment.name).all(),
            categories=categories, q=q, status=status, category=category)

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
        # Per-project breakdown
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
                               net=income - expense, project_breakdown=project_breakdown,
                               projects=projects)

    @app.route('/governance', methods=['GET', 'POST'])
    def governance():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('governance')
            return redirect(url_for('governance'))
        return render_template('governance.html', meetings=Meeting.query.order_by(Meeting.meeting_date.desc()).all())

    @app.route('/partnerships', methods=['GET', 'POST'])
    def partnerships():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            form_name = request.form['form_name']
            create_record('institutions' if form_name == 'institution' else 'partnerships')
            return redirect(url_for('partnerships'))
        return render_template('partnerships.html', institutions=Institution.query.order_by(Institution.name).all(), partnerships=Partnership.query.order_by(Partnership.id.desc()).all())

    @app.route('/protocol', methods=['GET', 'POST'])
    def protocol():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('protocol')
            return redirect(url_for('protocol'))
        return render_template('protocol.html', rules=ProtocolRule.query.order_by(ProtocolRule.id).all(), policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

    @app.route('/policies', methods=['GET', 'POST'])
    def policies():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('policies')
            return redirect(url_for('policies'))
        return render_template('policies.html', policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

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
            query = query.filter(
                RiskRegister.title.ilike(f'%{q}%') |
                RiskRegister.owner.ilike(f'%{q}%')
            )
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        return render_template('risks.html',
            risks=query.order_by(RiskRegister.severity.desc(), RiskRegister.id.desc()).all(),
            q=q, status=status, severity=severity)

    @app.route('/roadmap', methods=['GET', 'POST'])
    def roadmap():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('roadmap')
            return redirect(url_for('roadmap'))
        items = RoadmapItem.query.order_by(RoadmapItem.year.asc(), RoadmapItem.phase.asc()).all()
        return render_template('roadmap.html', items=items)

    @app.route('/events', methods=['GET', 'POST'])
    def events():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('events')
            return redirect(url_for('events'))
        return render_template('events.html', events=DisseminationEvent.query.order_by(DisseminationEvent.event_date.desc()).all())

    @app.route('/reports', methods=['GET', 'POST'])
    def reports():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            create_record('reports')
            return redirect(url_for('reports'))
        reports_list = MonthlyReport.query.order_by(MonthlyReport.created_at.desc()).all()
        current_month = date.today().strftime('%Y-%m')
        month_start = datetime.strptime(current_month + '-01', '%Y-%m-%d')
        month_bkgs = Booking.query.filter(Booking.start_dt >= month_start).count()
        month_evts = DisseminationEvent.query.filter(func.strftime('%Y-%m', DisseminationEvent.event_date) == current_month).count()
        return render_template('reports.html', reports=reports_list, month_bookings=month_bkgs, month_events=month_evts)

    @app.route('/audit')
    def audit():
        if not login_required():
            return redirect(url_for('login'))
        if not is_manager():
            flash('Access denied. Audit log is visible to managers only.', 'danger')
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
                    Booking.space == obj.space,
                    Booking.id != obj.id,
                    Booking.start_dt < obj.end_dt,
                    Booking.end_dt > obj.start_dt
                ).first()
                if conflict:
                    obj.project_id = original_project_id
                    db.session.rollback()
                    flash(f'Conflict detected with booking #{conflict.id} in {obj.space}.', 'danger')
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
        meeting_proposals = ProposalRecord.query.filter_by(meeting_id=obj.id).order_by(ProposalRecord.id).all() if kind == 'governance' else []
        attachments = Attachment.query.filter_by(entity_type=kind, entity_id=obj.id).order_by(Attachment.uploaded_at.desc()).all()
        audit_entries = AuditLog.query.filter_by(entity_type=kind, entity_id=obj.id).order_by(AuditLog.timestamp.desc()).limit(30).all()

        return render_template('record_detail.html',
            kind=kind, config=config, obj=obj, display_fields=display_fields, creator=creator,
            can_edit=can_edit_record(obj), is_manager=is_manager(),
            rs_sessions=rs_sessions, meeting_proposals=meeting_proposals,
            attachments=attachments, audit_entries=audit_entries)

    @app.route('/about')
    def about():
        if not login_required():
            return redirect(url_for('login'))
        return render_template('about.html')
