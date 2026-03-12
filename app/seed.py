from .models import db, User, Institution, Partnership, ResearchProject, Booking, Equipment, BudgetItem, Meeting, PolicyDocument, RiskRegister, RoadmapItem, ProtocolRule, DisseminationEvent, ResearchSession, ProposalRecord
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
    created = {}
    for name, email, role, pw in users:
        u = User(name=name, email=email, role=role)
        u.set_password(pw)
        db.session.add(u)
        created[email] = u
    db.session.flush()

    admin_id = created['admin@example.com'].id
    director_id = created['director@example.com'].id
    coordinator_id = created['coordinator@example.com'].id
    researcher_id = created['researcher@example.com'].id

    lmta = Institution(name='LMTA Mokslo centras', category='academic', contact_person='Director', contact_email='mc@lmta.lt', notes='Primary institutional partner for research infrastructure pilot.', created_by_id=director_id)
    vda = Institution(name='Vilnius Academy of Arts', category='academic', contact_person='Research Office', contact_email='research@vda.lt', notes='Potential Phase II national network partner.', created_by_id=coordinator_id)
    lmt = Institution(name='Lithuanian Research Council', category='funder', contact_person='Program Desk', contact_email='info@lmt.lt', notes='Potential co-funder for continuation and evaluation.', created_by_id=admin_id)
    db.session.add_all([lmta, vda, lmt])
    db.session.flush()

    db.session.add_all([
        Partnership(institution_id=lmta.id, status='active', objective='Establish 3-year external artistic research satellite and pilot governance model.', requested_support='Portable equipment, adaptation, coordination, reporting framework', timeline='2026-2029', created_by_id=director_id),
        Partnership(institution_id=vda.id, status='prospective', objective='Prepare Phase II interdisciplinary artistic research cooperation.', requested_support='Shared residencies and critical seminars', timeline='2028-2030', created_by_id=coordinator_id),
        Partnership(institution_id=lmt.id, status='prospective', objective='Seek Phase II infrastructure and methodology support.', requested_support='Evaluation and continuation funding', timeline='2028-2031', created_by_id=admin_id),
    ])

    p1 = ResearchProject(
        title='Embodied Sonic Methods Lab', lead='Artist Researcher', phase='phase_i', status='active',
        research_question='How can embodied performance techniques expand sonic research methodologies?',
        methods='Iterative rehearsals, listening sessions, annotated demonstrations',
        outputs='Lecture-performance, working paper, documentation archive',
        start_date=date.today() - timedelta(days=30), created_by_id=researcher_id
    )
    p2 = ResearchProject(
        title='Black Box for Artistic Research', lead='Research Coordinator', phase='phase_i', status='active',
        research_question='What spatial protocols best support practice-led research in temporary infrastructure?',
        methods='Studio testing, acoustic iterations, governance review',
        outputs='Protocol handbook, equipment transfer plan, presentation cycle',
        start_date=date.today() - timedelta(days=15), created_by_id=coordinator_id
    )
    db.session.add_all([p1, p2])
    db.session.flush()

    db.session.add_all([
        Booking(project_id=p1.id, space='Research Studio', booking_type='Residency Block', start_dt=datetime.now()+timedelta(days=1), end_dt=datetime.now()+timedelta(days=1, hours=4), lead_name='Artist Researcher', notes='Closed lab session', created_by_id=researcher_id),
        Booking(project_id=p2.id, space='Seminar Zone', booking_type='Method Workshop', start_dt=datetime.now()+timedelta(days=2), end_dt=datetime.now()+timedelta(days=2, hours=3), lead_name='Research Coordinator', notes='Protocol refinement meeting', created_by_id=coordinator_id),
    ])

    db.session.add_all([
        Equipment(name='Portable PA System', category='audio', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Transfer to successor Phase II site in 2029.', created_by_id=admin_id),
        Equipment(name='Modular Acoustic Panels', category='acoustics', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Retain as mobile research kit.', created_by_id=coordinator_id),
        Equipment(name='Seminar Tables', category='furniture', portable=True, status='available', owner='Ideas Block', transfer_plan='Move to future research lab.', created_by_id=admin_id),
    ])

    db.session.add_all([
        BudgetItem(category='Site Adaptation', direction='expense', amount=4200, note='Blackout, cable management, storage improvements', item_date=date.today()-timedelta(days=20), created_by_id=admin_id),
        BudgetItem(category='Portable Equipment', direction='expense', amount=7800, note='Audio, video, staging, documentation kit', item_date=date.today()-timedelta(days=12), created_by_id=admin_id),
        BudgetItem(category='MC Support', direction='income', amount=25000, note='Pilot infrastructure allocation', item_date=date.today()-timedelta(days=25), created_by_id=director_id),
        BudgetItem(category='Public Dissemination', direction='income', amount=1800, note='Ticketing and workshop revenue', item_date=date.today()-timedelta(days=6), created_by_id=coordinator_id),
    ])

    db.session.add_all([
        Meeting(title='Steering Group Kickoff', meeting_date=date.today()-timedelta(days=10), meeting_type='steering', body='Confirmed separation between research and public programming, monthly reporting cycle, and booking priorities.', decisions='Approve pilot governance stack and protected weekday research blocks.', created_by_id=director_id),
        Meeting(title='Protocol Review', meeting_date=date.today()-timedelta(days=3), meeting_type='operations', body='Reviewed scheduling, documentation obligations, and risk controls.', decisions='Adopt mandatory session logs and reset checklist.', created_by_id=coordinator_id),
    ])

    db.session.add_all([
        PolicyDocument(title='Research-First Scheduling Policy', category='operations', version='1.0', content='Weekday daytime use is reserved primarily for research sessions, residencies, and method workshops. Public events cannot displace previously approved research blocks.', created_by_id=director_id),
        PolicyDocument(title='Equipment Portability and Transfer Policy', category='legacy', version='1.0', content='All major equipment acquisitions must include owner assignment, portability status, and transfer destination for Phase II continuation.', created_by_id=admin_id),
        PolicyDocument(title='Documentation and Archiving Policy', category='research', version='1.0', content='All supported projects must submit a short process log and at least one documentation artifact per residency or lab cycle.', created_by_id=coordinator_id),
    ])

    db.session.add_all([
        RiskRegister(title='Research use displaced by event culture', severity='High', owner='Research Coordinator', mitigation='Protected time blocks, steering oversight, separate budgets, public dissemination capped on key weekdays.', status='open', created_by_id=director_id),
        RiskRegister(title='Sunk costs in temporary building', severity='Medium', owner='Director', mitigation='Prioritize portable equipment and minimal adaptation only.', status='open', created_by_id=admin_id),
        RiskRegister(title='Institutional skepticism due to DIY aesthetics', severity='Medium', owner='Admin User', mitigation='Maintain clean governance, visible reporting, visitor protocols, and professional documentation.', status='monitoring', created_by_id=admin_id),
    ])

    db.session.add_all([
        RoadmapItem(phase='phase_i', title='Pilot governance framework established', year=2026, owner='LMTA + Ideas Block', status='in_progress', details='Formal agreement, steering group, reporting routine.', created_by_id=director_id),
        RoadmapItem(phase='phase_i', title='Research studio adaptation completed', year=2026, owner='Operations Team', status='planned', details='Portable acoustic, blackout, staging, storage.', created_by_id=coordinator_id),
        RoadmapItem(phase='phase_ii', title='Secure successor site for permanent or semi-permanent lab', year=2028, owner='Steering Group', status='planned', details='Identify candidate host institutions and property options.', created_by_id=director_id),
        RoadmapItem(phase='phase_ii', title='Build national artistic research network', year=2029, owner='Partnership Lead', status='planned', details='LMTA, VDA, research council, independent partners.', created_by_id=coordinator_id),
        RoadmapItem(phase='phase_ii', title='Transfer equipment and protocol into next-stage platform', year=2029, owner='Technical Manager', status='planned', details='Move mobile kit, archive, and policy base to successor site.', created_by_id=admin_id),
    ])

    db.session.add_all([
        ProtocolRule(principle='Spatial Flexibility', description='Each room must support research, seminar, and dissemination modes with minimal reconfiguration effort.', implementation='Use modular staging, acoustic panels, stackable seminar furniture, and blackout systems.', created_by_id=coordinator_id),
        ProtocolRule(principle='Research-First Scheduling', description='Scheduling must prioritize research processes over event-driven revenue logic.', implementation='Reserve weekday daytime and approved intensive blocks for research use only.', created_by_id=director_id),
        ProtocolRule(principle='Documentation Culture', description='Every supported project produces an auditable trail of process, reflection, and outputs.', implementation='Session logs, recordings, annotated notes, and monthly reports.', created_by_id=coordinator_id),
        ProtocolRule(principle='Portable Infrastructure', description='Investments must survive demolition through mobility and transfer planning.', implementation='Maintain inventory with owner, portability, and successor destination.', created_by_id=admin_id),
        ProtocolRule(principle='Governance Transparency', description='Roles, decisions, and risks must be visible to all partners.', implementation='Publish meeting records, reports, policies, and risk register on the platform.', created_by_id=director_id),
    ])

    db.session.add_all([
        DisseminationEvent(title='Research Demonstration: Embodied Sonic Methods', event_date=date.today()+timedelta(days=14), format='Research Demonstration', audience='public + academic', linked_project='Embodied Sonic Methods Lab', notes='Annotated public sharing with post-event discussion.', created_by_id=researcher_id),
        DisseminationEvent(title='Protocol Colloquium', event_date=date.today()+timedelta(days=21), format='Seminar', audience='partner institutions', linked_project='Black Box for Artistic Research', notes='Invite LMTA, VDA, independent partners.', created_by_id=coordinator_id),
    ])

    # Get meeting and project IDs after flush
    db.session.flush()
    meeting1 = Meeting.query.filter_by(title='Steering Group Kickoff').first()
    meeting2 = Meeting.query.filter_by(title='Protocol Review').first()

    db.session.add_all([
        ResearchSession(project_id=p1.id, session_date=date.today()-timedelta(days=25), facilitator='Artist Researcher', participants='Artist Researcher, Research Coordinator', methods_used='Listening session, body-mapping', observations='Initial somatic responses to layered field recordings; participants noted spatial disorientation as generative.', open_questions='Can disorientation be structured? Is there a repeatable method here?', created_by_id=researcher_id),
        ResearchSession(project_id=p1.id, session_date=date.today()-timedelta(days=18), facilitator='Artist Researcher', participants='Artist Researcher, external collaborator', methods_used='Score-based performance, annotation', observations='Second iteration with graphic score. Score helped direct attention but constrained spontaneity.', open_questions='Score as constraint vs. score as map — test both approaches.', created_by_id=researcher_id),
        ResearchSession(project_id=p2.id, session_date=date.today()-timedelta(days=12), facilitator='Research Coordinator', participants='Research Coordinator, Admin User', methods_used='Spatial protocol testing, governance review', observations='Blackout system and acoustic panels tested with 3 different room configurations. Config C most effective for seminar mode.', open_questions='Does config C scale to larger groups? Test with 20+ participants.', created_by_id=coordinator_id),
    ])

    if meeting1 and meeting2:
        db.session.add_all([
            ProposalRecord(meeting_id=meeting1.id, proposal_text='Approve pilot governance framework and designate weekday 9:00–17:00 blocks as protected research time requiring coordinator approval to override.', proposer='MC Director', outcome='approved', votes_for=4, votes_against=0, dissenting_notes='', created_by_id=director_id),
            ProposalRecord(meeting_id=meeting1.id, proposal_text='Allocate separate budget lines for research activities vs. public programming to enable per-project cost tracking.', proposer='Admin User', outcome='approved', votes_for=3, votes_against=1, dissenting_notes='One member noted this adds administrative overhead; recommended quarterly rather than monthly reconciliation.', created_by_id=admin_id),
            ProposalRecord(meeting_id=meeting2.id, proposal_text='Mandate session logs for all supported projects — minimum one log entry per residency cycle.', proposer='Research Coordinator', outcome='approved', votes_for=4, votes_against=0, dissenting_notes='', created_by_id=coordinator_id),
            ProposalRecord(meeting_id=meeting2.id, proposal_text='Expand public programming to three evenings per week to increase revenue.', proposer='Admin User', outcome='rejected', votes_for=1, votes_against=3, dissenting_notes='Majority view: this directly conflicts with Research-First Scheduling Protocol and would displace ongoing residencies. Alternative: cap public events at one evening per week.', created_by_id=admin_id),
        ])

    db.session.commit()
