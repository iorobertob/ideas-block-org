from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from sqlalchemy import func
from .models import (
    db, User, Institution, Partnership, ResearchProject, Booking, Equipment,
    BudgetItem, Meeting, PolicyDocument, RiskRegister, RoadmapItem,
    ProtocolRule, DisseminationEvent, MonthlyReport
)


def current_user():
    uid = session.get('user_id')
    if uid:
        return db.session.get(User, uid)
    return None


def login_required():
    return current_user() is not None


def admin_required():
    user = current_user()
    return user and user.role in {'admin', 'director', 'coordinator'}


def parse_date(v):
    return datetime.strptime(v, '%Y-%m-%d').date() if v else None


def parse_dt(v):
    return datetime.strptime(v, '%Y-%m-%dT%H:%M') if v else None


def register_routes(app):
    @app.context_processor
    def inject_user():
        return {'current_user': current_user()}

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
            if not admin_required():
                flash('You do not have permission to create users.', 'danger')
                return redirect(url_for('users'))
            user = User(name=request.form['name'], email=request.form['email'].strip().lower(), role=request.form['role'])
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            flash('User created.', 'success')
            return redirect(url_for('users'))
        return render_template('users.html', users=User.query.order_by(User.name).all())

    @app.route('/projects', methods=['GET', 'POST'])
    def projects():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            p = ResearchProject(
                title=request.form['title'], lead=request.form['lead'], phase=request.form['phase'],
                status=request.form['status'], research_question=request.form['research_question'],
                methods=request.form.get('methods', ''), outputs=request.form.get('outputs', ''),
                start_date=parse_date(request.form.get('start_date')) or date.today(),
                end_date=parse_date(request.form.get('end_date'))
            )
            db.session.add(p)
            db.session.commit()
            flash('Project created.', 'success')
            return redirect(url_for('projects'))
        return render_template('projects.html', projects=ResearchProject.query.order_by(ResearchProject.start_date.desc()).all())

    @app.route('/bookings', methods=['GET', 'POST'])
    def bookings():
        if not login_required():
            return redirect(url_for('login'))
        projects = ResearchProject.query.order_by(ResearchProject.title).all()
        if request.method == 'POST':
            start_dt = parse_dt(request.form['start_dt'])
            end_dt = parse_dt(request.form['end_dt'])
            space = request.form['space']
            conflict = Booking.query.filter(
                Booking.space == space,
                Booking.start_dt < end_dt,
                Booking.end_dt > start_dt
            ).first()
            if conflict:
                flash(f'Conflict detected with booking #{conflict.id} in {space}.', 'danger')
            else:
                b = Booking(
                    project_id=int(request.form['project_id']), space=space,
                    booking_type=request.form['booking_type'], start_dt=start_dt, end_dt=end_dt,
                    lead_name=request.form['lead_name'], notes=request.form.get('notes', '')
                )
                db.session.add(b)
                db.session.commit()
                flash('Booking added.', 'success')
            return redirect(url_for('bookings'))
        bookings = Booking.query.order_by(Booking.start_dt.asc()).all()
        return render_template('bookings.html', bookings=bookings, projects=projects)

    @app.route('/equipment', methods=['GET', 'POST'])
    def equipment():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            e = Equipment(
                name=request.form['name'], category=request.form['category'],
                portable=('portable' in request.form), status=request.form['status'],
                owner=request.form['owner'], transfer_plan=request.form.get('transfer_plan', '')
            )
            db.session.add(e)
            db.session.commit()
            flash('Equipment item added.', 'success')
            return redirect(url_for('equipment'))
        return render_template('equipment.html', equipment=Equipment.query.order_by(Equipment.category, Equipment.name).all())

    @app.route('/budget', methods=['GET', 'POST'])
    def budget():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            item = BudgetItem(
                category=request.form['category'], direction=request.form['direction'],
                amount=float(request.form['amount']), note=request.form.get('note', ''),
                item_date=parse_date(request.form.get('item_date')) or date.today()
            )
            db.session.add(item)
            db.session.commit()
            flash('Budget item recorded.', 'success')
            return redirect(url_for('budget'))
        items = BudgetItem.query.order_by(BudgetItem.item_date.desc()).all()
        income = sum(i.amount for i in items if i.direction == 'income')
        expense = sum(i.amount for i in items if i.direction == 'expense')
        return render_template('budget.html', items=items, income=income, expense=expense, net=income-expense)

    @app.route('/governance', methods=['GET', 'POST'])
    def governance():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            m = Meeting(
                title=request.form['title'], meeting_date=parse_date(request.form['meeting_date']) or date.today(),
                body=request.form['body'], decisions=request.form.get('decisions', ''), meeting_type=request.form['meeting_type']
            )
            db.session.add(m)
            db.session.commit()
            flash('Meeting record added.', 'success')
            return redirect(url_for('governance'))
        return render_template('governance.html', meetings=Meeting.query.order_by(Meeting.meeting_date.desc()).all())

    @app.route('/partnerships', methods=['GET', 'POST'])
    def partnerships():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            if request.form['form_name'] == 'institution':
                i = Institution(name=request.form['name'], category=request.form['category'], contact_person=request.form.get('contact_person', ''), contact_email=request.form.get('contact_email', ''), notes=request.form.get('notes', ''))
                db.session.add(i)
                db.session.commit()
                flash('Institution added.', 'success')
            else:
                p = Partnership(institution_id=int(request.form['institution_id']), status=request.form['status'], objective=request.form['objective'], requested_support=request.form.get('requested_support', ''), timeline=request.form.get('timeline', ''))
                db.session.add(p)
                db.session.commit()
                flash('Partnership record added.', 'success')
            return redirect(url_for('partnerships'))
        return render_template('partnerships.html', institutions=Institution.query.order_by(Institution.name).all(), partnerships=Partnership.query.order_by(Partnership.id.desc()).all())

    @app.route('/protocol', methods=['GET', 'POST'])
    def protocol():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            r = ProtocolRule(principle=request.form['principle'], description=request.form['description'], implementation=request.form.get('implementation', ''))
            db.session.add(r)
            db.session.commit()
            flash('Protocol rule added.', 'success')
            return redirect(url_for('protocol'))
        return render_template('protocol.html', rules=ProtocolRule.query.order_by(ProtocolRule.id).all(), policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

    @app.route('/policies', methods=['GET', 'POST'])
    def policies():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            p = PolicyDocument(title=request.form['title'], category=request.form['category'], content=request.form['content'], version=request.form.get('version', '1.0'))
            db.session.add(p)
            db.session.commit()
            flash('Policy saved.', 'success')
            return redirect(url_for('policies'))
        return render_template('policies.html', policies=PolicyDocument.query.order_by(PolicyDocument.category, PolicyDocument.title).all())

    @app.route('/risks', methods=['GET', 'POST'])
    def risks():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            r = RiskRegister(title=request.form['title'], severity=request.form['severity'], owner=request.form['owner'], mitigation=request.form['mitigation'], status=request.form['status'])
            db.session.add(r)
            db.session.commit()
            flash('Risk logged.', 'success')
            return redirect(url_for('risks'))
        return render_template('risks.html', risks=RiskRegister.query.order_by(RiskRegister.severity.desc(), RiskRegister.id.desc()).all())

    @app.route('/roadmap', methods=['GET', 'POST'])
    def roadmap():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            r = RoadmapItem(phase=request.form['phase'], title=request.form['title'], year=int(request.form['year']), owner=request.form['owner'], status=request.form['status'], details=request.form.get('details', ''))
            db.session.add(r)
            db.session.commit()
            flash('Roadmap item created.', 'success')
            return redirect(url_for('roadmap'))
        items = RoadmapItem.query.order_by(RoadmapItem.year.asc(), RoadmapItem.phase.asc()).all()
        return render_template('roadmap.html', items=items)

    @app.route('/events', methods=['GET', 'POST'])
    def events():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            e = DisseminationEvent(title=request.form['title'], event_date=parse_date(request.form['event_date']) or date.today(), format=request.form['format'], audience=request.form.get('audience', 'public'), linked_project=request.form.get('linked_project', ''), notes=request.form.get('notes', ''))
            db.session.add(e)
            db.session.commit()
            flash('Event added.', 'success')
            return redirect(url_for('events'))
        return render_template('events.html', events=DisseminationEvent.query.order_by(DisseminationEvent.event_date.desc()).all())

    @app.route('/reports', methods=['GET', 'POST'])
    def reports():
        if not login_required():
            return redirect(url_for('login'))
        if request.method == 'POST':
            month = request.form['month']
            summary = request.form['summary']
            rep = MonthlyReport(month=month, summary=summary)
            db.session.add(rep)
            db.session.commit()
            flash('Report saved.', 'success')
            return redirect(url_for('reports'))
        reports = MonthlyReport.query.order_by(MonthlyReport.created_at.desc()).all()
        # auto summary data
        current_month = date.today().strftime('%Y-%m')
        month_start = datetime.strptime(current_month + '-01', '%Y-%m-%d')
        month_bookings = Booking.query.filter(Booking.start_dt >= month_start).count()
        month_events = DisseminationEvent.query.filter(func.strftime('%Y-%m', DisseminationEvent.event_date) == current_month).count()
        return render_template('reports.html', reports=reports, month_bookings=month_bookings, month_events=month_events)

    @app.route('/about')
    def about():
        if not login_required():
            return redirect(url_for('login'))
        return render_template('about.html')
