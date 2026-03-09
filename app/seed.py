from .models import db, User, Institution, Partnership, ResearchProject, Booking, Equipment, BudgetItem, Meeting, PolicyDocument, RiskRegister, RoadmapItem, ProtocolRule, DisseminationEvent
from datetime import datetime, date, timedelta


def seed_if_empty():
    if User.query.first():
        return

    users = [
        ('Admin User', 'admin@example.com', 'admin', 'admin123'),
        ('MC Director', 'director@example.com', 'director', 'director123'),
        ('Research Coordinator', 'coordinator@example.com', 'coordinator', 'coord123'),
        ('Artist Researcher', 'researcher@example.com', 'member', 'research123'),
    ]
    for name, email, role, pw in users:
        u = User(name=name, email=email, role=role)
        u.set_password(pw)
        db.session.add(u)

    lmta = Institution(name='LMTA Mokslo centras', category='academic', contact_person='Director', contact_email='mc@lmta.lt', notes='Primary institutional partner for research infrastructure pilot.')
    vda = Institution(name='Vilnius Academy of Arts', category='academic', contact_person='Research Office', contact_email='research@vda.lt', notes='Potential Phase II national network partner.')
    lmt = Institution(name='Lithuanian Research Council', category='funder', contact_person='Program Desk', contact_email='info@lmt.lt', notes='Potential co-funder for continuation and evaluation.')
    db.session.add_all([lmta, vda, lmt])
    db.session.flush()

    db.session.add_all([
        Partnership(institution_id=lmta.id, status='active', objective='Establish 3-year external artistic research satellite and pilot governance model.', requested_support='Portable equipment, adaptation, coordination, reporting framework', timeline='2026-2029'),
        Partnership(institution_id=vda.id, status='prospective', objective='Prepare Phase II interdisciplinary artistic research cooperation.', requested_support='Shared residencies and critical seminars', timeline='2028-2030'),
        Partnership(institution_id=lmt.id, status='prospective', objective='Seek Phase II infrastructure and methodology support.', requested_support='Evaluation and continuation funding', timeline='2028-2031'),
    ])

    p1 = ResearchProject(
        title='Embodied Sonic Methods Lab', lead='Dr. A. Researcher', phase='phase_i', status='active',
        research_question='How can embodied performance techniques expand sonic research methodologies?',
        methods='Iterative rehearsals, listening sessions, annotated demonstrations',
        outputs='Lecture-performance, working paper, documentation archive',
        start_date=date.today() - timedelta(days=30)
    )
    p2 = ResearchProject(
        title='Black Box for Artistic Research', lead='Ideas Block / LMTA team', phase='phase_i', status='active',
        research_question='What spatial protocols best support practice-led research in temporary infrastructure?',
        methods='Studio testing, acoustic iterations, governance review',
        outputs='Protocol handbook, equipment transfer plan, presentation cycle',
        start_date=date.today() - timedelta(days=15)
    )
    db.session.add_all([p1, p2])
    db.session.flush()

    db.session.add_all([
        Booking(project_id=p1.id, space='Research Studio', booking_type='Residency Block', start_dt=datetime.now()+timedelta(days=1), end_dt=datetime.now()+timedelta(days=1, hours=4), lead_name='Dr. A. Researcher', notes='Closed lab session'),
        Booking(project_id=p2.id, space='Seminar Zone', booking_type='Method Workshop', start_dt=datetime.now()+timedelta(days=2), end_dt=datetime.now()+timedelta(days=2, hours=3), lead_name='Research Coordinator', notes='Protocol refinement meeting'),
    ])

    db.session.add_all([
        Equipment(name='Portable PA System', category='audio', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Transfer to successor Phase II site in 2029.'),
        Equipment(name='Modular Acoustic Panels', category='acoustics', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Retain as mobile research kit.'),
        Equipment(name='Seminar Tables', category='furniture', portable=True, status='available', owner='Ideas Block', transfer_plan='Move to future research lab.'),
    ])

    db.session.add_all([
        BudgetItem(category='Site Adaptation', direction='expense', amount=4200, note='Blackout, cable management, storage improvements', item_date=date.today()-timedelta(days=20)),
        BudgetItem(category='Portable Equipment', direction='expense', amount=7800, note='Audio, video, staging, documentation kit', item_date=date.today()-timedelta(days=12)),
        BudgetItem(category='MC Support', direction='income', amount=25000, note='Pilot infrastructure allocation', item_date=date.today()-timedelta(days=25)),
        BudgetItem(category='Public Dissemination', direction='income', amount=1800, note='Ticketing and workshop revenue', item_date=date.today()-timedelta(days=6)),
    ])

    db.session.add_all([
        Meeting(title='Steering Group Kickoff', meeting_date=date.today()-timedelta(days=10), meeting_type='steering', body='Confirmed separation between research and public programming, monthly reporting cycle, and booking priorities.', decisions='Approve pilot governance stack and protected weekday research blocks.'),
        Meeting(title='Protocol Review', meeting_date=date.today()-timedelta(days=3), meeting_type='operations', body='Reviewed scheduling, documentation obligations, and risk controls.', decisions='Adopt mandatory session logs and reset checklist.'),
    ])

    db.session.add_all([
        PolicyDocument(title='Research-First Scheduling Policy', category='operations', version='1.0', content='Weekday daytime use is reserved primarily for research sessions, residencies, and method workshops. Public events cannot displace previously approved research blocks.'),
        PolicyDocument(title='Equipment Portability and Transfer Policy', category='legacy', version='1.0', content='All major equipment acquisitions must include owner assignment, portability status, and transfer destination for Phase II continuation.'),
        PolicyDocument(title='Documentation and Archiving Policy', category='research', version='1.0', content='All supported projects must submit a short process log and at least one documentation artifact per residency or lab cycle.'),
    ])

    db.session.add_all([
        RiskRegister(title='Research use displaced by event culture', severity='High', owner='Research Coordinator', mitigation='Protected time blocks, steering oversight, separate budgets, public dissemination capped on key weekdays.', status='open'),
        RiskRegister(title='Sunk costs in temporary building', severity='Medium', owner='Director', mitigation='Prioritize portable equipment and minimal adaptation only.', status='open'),
        RiskRegister(title='Institutional skepticism due to DIY aesthetics', severity='Medium', owner='Admin User', mitigation='Maintain clean governance, visible reporting, visitor protocols, and professional documentation.', status='monitoring'),
    ])

    db.session.add_all([
        RoadmapItem(phase='phase_i', title='Pilot governance framework established', year=2026, owner='LMTA + Ideas Block', status='in_progress', details='Formal agreement, steering group, reporting routine.'),
        RoadmapItem(phase='phase_i', title='Research studio adaptation completed', year=2026, owner='Operations Team', status='planned', details='Portable acoustic, blackout, staging, storage.'),
        RoadmapItem(phase='phase_ii', title='Secure successor site for permanent or semi-permanent lab', year=2028, owner='Steering Group', status='planned', details='Identify candidate host institutions and property options.'),
        RoadmapItem(phase='phase_ii', title='Build national artistic research network', year=2029, owner='Partnership Lead', status='planned', details='LMTA, VDA, research council, independent partners.'),
        RoadmapItem(phase='phase_ii', title='Transfer equipment and protocol into next-stage platform', year=2029, owner='Technical Manager', status='planned', details='Move mobile kit, archive, and policy base to successor site.'),
    ])

    db.session.add_all([
        ProtocolRule(principle='Spatial Flexibility', description='Each room must support research, seminar, and dissemination modes with minimal reconfiguration effort.', implementation='Use modular staging, acoustic panels, stackable seminar furniture, and blackout systems.'),
        ProtocolRule(principle='Research-First Scheduling', description='Scheduling must prioritize research processes over event-driven revenue logic.', implementation='Reserve weekday daytime and approved intensive blocks for research use only.'),
        ProtocolRule(principle='Documentation Culture', description='Every supported project produces an auditable trail of process, reflection, and outputs.', implementation='Session logs, recordings, annotated notes, and monthly reports.'),
        ProtocolRule(principle='Portable Infrastructure', description='Investments must survive demolition through mobility and transfer planning.', implementation='Maintain inventory with owner, portability, and successor destination.'),
        ProtocolRule(principle='Governance Transparency', description='Roles, decisions, and risks must be visible to all partners.', implementation='Publish meeting records, reports, policies, and risk register on the platform.'),
    ])

    db.session.add_all([
        DisseminationEvent(title='Research Demonstration: Embodied Sonic Methods', event_date=date.today()+timedelta(days=14), format='Research Demonstration', audience='public + academic', linked_project='Embodied Sonic Methods Lab', notes='Annotated public sharing with post-event discussion.'),
        DisseminationEvent(title='Protocol Colloquium', event_date=date.today()+timedelta(days=21), format='Seminar', audience='partner institutions', linked_project='Black Box for Artistic Research', notes='Invite LMTA, VDA, independent partners.'),
    ])

    db.session.commit()
