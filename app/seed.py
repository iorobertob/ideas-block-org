from .models import (
    db, User, Institution, Partnership, ResearchProject, Booking, Equipment,
    BudgetItem, Meeting, PolicyDocument, RiskRegister, RoadmapItem,
    ProtocolRule, DisseminationEvent, ResearchSession, ProposalRecord,
    Facility, WorkingGroup, WorkingGroupMembership, ProjectMembership,
    Milestone, Task, ConstitutionDocument, Poll, PollOption, PollVote, PollToken,
    LegacyTask, CallForSubmission
)
from datetime import datetime, date, timedelta
import uuid


def _seed_calls(admin_id, coordinator_id):
    if CallForSubmission.query.first():
        return
    db.session.add_all([
        CallForSubmission(
            title='JAR', full_name='Journal for Artistic Research',
            venue_type='journal', deadline_status='fixed',
            area='artistic research, practice-based research, exposition-based publication',
            known_deadline=date(2026, 5, 31),
            source_url='https://www.jar-online.net/en/calls',
            description='Three annual submission deadlines (May 31, Sep 30, Jan 31). Extremely high relevance for artistic research outputs and exposition-format work.',
            guidelines='Expositions submitted via the Research Catalogue platform. No word limit but scope is evaluated. Peer-reviewed.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='NIME 2026', full_name='International Conference on New Interfaces for Musical Expression',
            venue_type='conference', deadline_status='fixed',
            area='musical interfaces, experimental instruments, embodied interaction, performance, installations',
            known_deadline=date(2026, 6, 23),
            source_url='https://nime2026.org/',
            description='NIME is the premier conference on new musical interfaces. Workshops due 2026-03-05; conference 2026-06-23 to 06-26.',
            guidelines='Paper, music, and installation submissions via EasyChair. Camera-ready due 2026-04-30. Check call pages for format requirements.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='DAFx26', full_name='International Conference on Digital Audio Effects',
            venue_type='conference', deadline_status='fixed',
            area='audio effects, signal processing, MIR-adjacent audio research',
            known_deadline=date(2026, 9, 1),
            source_url='https://dafx26.mit.edu/',
            description='Conference runs 2026-09-01 to 09-04. Paper submissions closed 2026-03-30; demo submissions due 2026-05-18.',
            guidelines='Full paper or demo paper. LaTeX template required. Max 8 pages for papers. Demo submissions accepted until 2026-05-22.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='ISMIR 2026', full_name='International Society for Music Information Retrieval Conference',
            venue_type='conference', deadline_status='fixed',
            area='MIR, computational music analysis, generation, algorithms',
            known_deadline=date(2026, 4, 27),
            source_url='https://ismir2026.ismir.net/',
            description='The main MIR conference. Paper submission deadline 2026-04-27. Early-bird registration 2026-07-10.',
            guidelines='6-page paper + references. Double-blind review. Reproducibility encouraged. Submission via CMT.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='ICMC 2026', full_name='International Computer Music Conference',
            venue_type='conference', deadline_status='fixed',
            area='computer music, algorithmic composition, electronic music, music tech',
            known_deadline=date(2026, 4, 1),
            source_url='https://www.icmc2026.com/',
            description='Abstracts were due 2026-02-15; camera-ready due 2026-04-01. Core venue for computer music research and practice.',
            guidelines='Submit via EasyChair. Paper and music / installation calls. Check site for exact format.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='SMC 2026', full_name='Sound and Music Computing Conference',
            venue_type='conference', deadline_status='fixed',
            area='sound and music computing, AI + music, sonic creativity, performances and installations',
            known_deadline=date(2026, 3, 13),
            source_url='https://smc26.mbz.hr/',
            description='Paper and music submission deadline 2026-03-13. Strong venue for sound/music computing intersecting artistic practice.',
            guidelines='Full papers and extended abstracts accepted. Music/installation call open separately. LaTeX or Word template.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='I3DA 2026', full_name='International Conference on Immersive and 3D Audio',
            venue_type='conference', deadline_status='fixed',
            area='immersive audio, spatial audio, VR/AR audio, 3D sound',
            known_deadline=date(2026, 5, 18),
            source_url='https://www.i3da2026.org/cfp.html',
            description='Abstract due 2026-04-03; full paper due 2026-05-18. Core venue for spatial and immersive audio research.',
            guidelines='4–6 page papers, IEEE format. Abstract submission required before full paper.',
            recurrence='biennial',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='Organised Sound',
            venue_type='journal', deadline_status='special-issue-based',
            area='electroacoustic music, sonic arts, sound art, music technology',
            source_url='https://www.cambridge.org/core/journals/organised-sound',
            description='Cambridge journal for electroacoustic and sonic arts. Themed issues vary; current special issue on "Electroacoustic Audiovisual Composition and Intermediality" (deadline 2026-01-15 has passed).',
            guidelines='Check current call on Cambridge Core. Standard academic paper format, 6000–8000 words typical.',
            recurrence='none',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='Leonardo', full_name='Leonardo / MIT Press',
            venue_type='journal', deadline_status='rolling',
            area='art-science-technology, experimental media, hybrid theory/practice',
            source_url='https://leonardo.info/faqs',
            description='Rolling submissions; no fixed deadline. Extremely high relevance for art-science-technology intersections.',
            guidelines='Unsolicited submissions accepted. 2000–6000 words. Check submission guidelines on Leonardo website.',
            recurrence='none',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='TISMIR', full_name='Transactions of the International Society for Music Information Retrieval',
            venue_type='journal', deadline_status='rolling',
            area='music information retrieval, computational music analysis, music AI',
            source_url='https://transactions.ismir.net/',
            description='Open-access MIR journal with rolling submissions. Complements ISMIR conference.',
            guidelines='Full research papers. LaTeX template. Single-blind or double-blind depending on submission type.',
            recurrence='none',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='Prix Ars Electronica 2027', full_name='Prix Ars Electronica — Digital Musics & Sound Art / AI & Intelligence',
            venue_type='prize', deadline_status='seasonal-check',
            area='media art, digital music and sound art, AI art, interactive art',
            known_deadline=date(2027, 3, 1),
            source_url='https://ars.electronica.art/prix/en/',
            description='Annual prize. 2026 extended deadline was 2026-03-09. Next open call expected January 2027. Relevant categories: Digital Musics & Sound Art, Artificial Life & Intelligence, Interactive Art+.',
            guidelines='Online submission platform. Projects, artworks, and research outputs eligible. Check category-specific guidelines each year.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='ZKM Open Calls', full_name='ZKM | Zentrum für Kunst und Medien — Open Calls',
            venue_type='residency', deadline_status='seasonal-check',
            area='media art, sound research, installations, theory and practice',
            source_url='https://zkm.de/en/open-calls',
            description='ZKM regularly posts residency and research calls. Recent: Exoplanetary Voices (2026-03-20), Rauschenberg Residencies (2026-04-12), Summer School TIME³ (2026-05-06).',
            guidelines='Varies per call. Check zkm.de/en/open-calls for current opportunities.',
            recurrence='none',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='EMAP Residencies', full_name='European Media Art Platform — Artist Residencies',
            venue_type='residency', deadline_status='seasonal-check',
            area='media art residencies, collaborative production, experimental technology art',
            source_url='https://call.emare.eu/',
            description='Important European residency platform. PhD candidates explicitly eligible. 2027 residencies open call expected autumn 2026.',
            guidelines='Online application via emare.eu. Project proposal + portfolio. International collaborations encouraged.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='CMMAS / Visiones Sonoras', full_name='Centro Mexicano para la Música y las Artes Sonoras',
            venue_type='festival', deadline_status='seasonal-check',
            area='electroacoustic music, sound art, residencies, festivals, workshops',
            source_url='https://www.cmmas.org/convocatorias',
            description='Major Ibero-American node for sound art and contemporary music. Regular calls for Visiones Sonoras festival, residencies, and composition programs. Check convocatorias page each spring.',
            guidelines='Varies per call. Spanish and English accepted. Check cmmas.org/convocatorias for current opportunities.',
            recurrence='annual',
            created_by_id=coordinator_id),
        CallForSubmission(
            title='ISEA', full_name='International Symposium on Electronic / Emerging Art',
            venue_type='conference', deadline_status='seasonal-check',
            area='electronic art, media art, sound art, hybrid practices',
            source_url='https://isea-archives.org/',
            description='Essential umbrella event for media art, sound, and hybrid art research ecosystems. Annual; call timing varies by host city.',
            guidelines='Paper and artwork/installation submissions. Check current ISEA host website for year-specific guidelines.',
            recurrence='annual',
            created_by_id=coordinator_id),
    ])
    db.session.commit()


def seed_if_empty():
    first_user = User.query.first()
    if not first_user:
        _seed_full()
        return
    # Seed calls independently even if users already exist
    admin = User.query.filter_by(role='admin').first() or first_user
    coordinator = User.query.filter(User.role.in_(['coordinator', 'admin'])).first() or first_user
    _seed_calls(admin.id, coordinator.id)


def _seed_full():
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

    # ── Institutions ──
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

    # ── Facilities ──
    f1 = Facility(name='Research Studio A', capacity=15, floor_area='80m²', location='Kompresorinė, ground floor',
                  modes='residency, listening session, rehearsal, documentation',
                  characteristics='Blackout system, modular acoustic panels, portable staging',
                  description='Primary research and residency space. Research-first use during weekday 9–17.',
                  status='active', created_by_id=coordinator_id)
    f2 = Facility(name='Seminar Zone', capacity=30, floor_area='60m²', location='Kompresorinė, first floor',
                  modes='seminar, workshop, colloquium, presentation',
                  characteristics='Natural light, modular seating, projector, whiteboard',
                  description='Multi-use seminar space for governance meetings, workshops, and public programs.',
                  status='active', created_by_id=coordinator_id)
    f3 = Facility(name='Documentation Lab', capacity=6, floor_area='25m²', location='Kompresorinė, ground floor',
                  modes='video editing, audio post-production, archiving',
                  characteristics='Blackout, NAS storage, workstations',
                  description='Post-production space for research documentation, recordings, and archiving.',
                  status='active', created_by_id=admin_id)
    db.session.add_all([f1, f2, f3])
    db.session.flush()

    # ── Equipment ──
    db.session.add_all([
        Equipment(name='Portable PA System', category='audio', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Transfer to successor Phase II site in 2029.', facility_id=f1.id, created_by_id=admin_id),
        Equipment(name='Modular Acoustic Panels', category='acoustics', portable=True, status='available', owner='LMTA / Ideas Block', transfer_plan='Retain as mobile research kit.', facility_id=f1.id, created_by_id=coordinator_id),
        Equipment(name='Seminar Tables', category='furniture', portable=True, status='available', owner='Ideas Block', transfer_plan='Move to future research lab.', facility_id=f2.id, created_by_id=admin_id),
        Equipment(name='4K Documentation Camera', category='video', portable=True, status='available', owner='Ideas Block', transfer_plan='Transfer with documentation lab.', facility_id=f3.id, created_by_id=admin_id),
        Equipment(name='Portable Field Recorders (x3)', category='audio', portable=True, status='available', owner='LMTA', transfer_plan='Reassign to Phase II partner institution.', facility_id=f1.id, created_by_id=researcher_id),
    ])

    # ── Projects ──
    p1 = ResearchProject(
        title='Embodied Sonic Methods Lab', lead='Artist Researcher', phase='phase_i', status='active',
        research_question='How can embodied performance techniques expand sonic research methodologies?',
        methods='Iterative rehearsals, listening sessions, annotated demonstrations',
        outputs='Lecture-performance, working paper, documentation archive',
        budget_allocation=3500.0,
        start_date=date.today() - timedelta(days=30), created_by_id=researcher_id
    )
    p2 = ResearchProject(
        title='Black Box for Artistic Research', lead='Research Coordinator', phase='phase_i', status='active',
        research_question='What spatial protocols best support practice-led research in temporary infrastructure?',
        methods='Studio testing, acoustic iterations, governance review',
        outputs='Protocol handbook, equipment transfer plan, presentation cycle',
        budget_allocation=4800.0,
        start_date=date.today() - timedelta(days=15), created_by_id=coordinator_id
    )
    db.session.add_all([p1, p2])
    db.session.flush()

    # ── Project memberships ──
    db.session.add_all([
        ProjectMembership(project_id=p1.id, user_id=researcher_id, role='lead researcher'),
        ProjectMembership(project_id=p1.id, user_id=coordinator_id, role='advisor'),
        ProjectMembership(project_id=p2.id, user_id=coordinator_id, role='lead researcher'),
        ProjectMembership(project_id=p2.id, user_id=admin_id, role='production support'),
    ])

    # ── Bookings ──
    db.session.add_all([
        Booking(project_id=p1.id, space='Research Studio A', booking_type='Residency Block', start_dt=datetime.now()+timedelta(days=1), end_dt=datetime.now()+timedelta(days=1, hours=4), lead_name='Artist Researcher', notes='Closed lab session', created_by_id=researcher_id),
        Booking(project_id=p2.id, space='Seminar Zone', booking_type='Method Workshop', start_dt=datetime.now()+timedelta(days=2), end_dt=datetime.now()+timedelta(days=2, hours=3), lead_name='Research Coordinator', notes='Protocol refinement meeting', created_by_id=coordinator_id),
    ])

    # ── Budget ──
    db.session.add_all([
        BudgetItem(category='Site Adaptation', direction='expense', amount=4200, note='Blackout, cable management, storage improvements', item_date=date.today()-timedelta(days=20), project_id=p2.id, created_by_id=admin_id),
        BudgetItem(category='Portable Equipment', direction='expense', amount=7800, note='Audio, video, staging, documentation kit', item_date=date.today()-timedelta(days=12), created_by_id=admin_id),
        BudgetItem(category='MC Support', direction='income', amount=25000, note='Pilot infrastructure allocation', item_date=date.today()-timedelta(days=25), created_by_id=director_id),
        BudgetItem(category='Public Dissemination', direction='income', amount=1800, note='Ticketing and workshop revenue', item_date=date.today()-timedelta(days=6), created_by_id=coordinator_id),
        BudgetItem(category='Research Materials', direction='expense', amount=680, note='Consumables and documentation', item_date=date.today()-timedelta(days=8), project_id=p1.id, created_by_id=researcher_id),
    ])

    # ── Working Groups ──
    wg1 = WorkingGroup(name='Research Methods Working Group', description='Develops and reviews research methodologies across all active projects.', focus='research methodology, documentation standards, session protocols', status='active', created_by_id=coordinator_id)
    wg2 = WorkingGroup(name='Phase II Transition Group', description='Prepares institutional strategy for Phase II: successor site, network building, legacy handoff.', focus='Phase II strategy, partnerships, equipment transfer, funding', status='active', created_by_id=director_id)
    db.session.add_all([wg1, wg2])
    db.session.flush()

    db.session.add_all([
        WorkingGroupMembership(wg_id=wg1.id, user_id=coordinator_id, role='convenor'),
        WorkingGroupMembership(wg_id=wg1.id, user_id=researcher_id, role='member'),
        WorkingGroupMembership(wg_id=wg2.id, user_id=director_id, role='chair'),
        WorkingGroupMembership(wg_id=wg2.id, user_id=admin_id, role='member'),
        WorkingGroupMembership(wg_id=wg2.id, user_id=coordinator_id, role='member'),
    ])

    # ── Meetings ──
    m1 = Meeting(title='Steering Group Kickoff', meeting_date=date.today()-timedelta(days=10), meeting_type='steering', body='Confirmed separation between research and public programming, monthly reporting cycle, and booking priorities.', decisions='Approve pilot governance stack and protected weekday research blocks.', created_by_id=director_id)
    m2 = Meeting(title='Protocol Review', meeting_date=date.today()-timedelta(days=3), meeting_type='operations', body='Reviewed scheduling, documentation obligations, and risk controls.', decisions='Adopt mandatory session logs and reset checklist.', working_group_id=wg1.id, created_by_id=coordinator_id)
    db.session.add_all([m1, m2])
    db.session.flush()

    # ── Policies ──
    db.session.add_all([
        PolicyDocument(title='Research-First Scheduling Policy', category='operations', version='1.0', content='Weekday daytime use is reserved primarily for research sessions, residencies, and method workshops. Public events cannot displace previously approved research blocks.', created_by_id=director_id),
        PolicyDocument(title='Equipment Portability and Transfer Policy', category='legacy', version='1.0', content='All major equipment acquisitions must include owner assignment, portability status, and transfer destination for Phase II continuation.', created_by_id=admin_id),
        PolicyDocument(title='Documentation and Archiving Policy', category='research', version='1.0', content='All supported projects must submit a short process log and at least one documentation artifact per residency or lab cycle.', created_by_id=coordinator_id),
    ])

    # ── Risks ──
    db.session.add_all([
        RiskRegister(title='Research use displaced by event culture', severity='High', owner='Research Coordinator', mitigation='Protected time blocks, steering oversight, separate budgets, public dissemination capped on key weekdays.', status='open', created_by_id=director_id),
        RiskRegister(title='Sunk costs in temporary building', severity='Medium', owner='Director', mitigation='Prioritize portable equipment and minimal adaptation only.', status='open', created_by_id=admin_id),
        RiskRegister(title='Institutional skepticism due to DIY aesthetics', severity='Medium', owner='Admin User', mitigation='Maintain clean governance, visible reporting, visitor protocols, and professional documentation.', status='monitoring', created_by_id=admin_id),
    ])

    # ── Roadmap ──
    db.session.add_all([
        RoadmapItem(phase='phase_i', title='Pilot governance framework established', year=2026, owner='LMTA + Ideas Block', status='in_progress', details='Formal agreement, steering group, reporting routine.', start_date=date(2026, 1, 1), end_date=date(2026, 6, 30), created_by_id=director_id),
        RoadmapItem(phase='phase_i', title='Research studio adaptation completed', year=2026, owner='Operations Team', status='planned', details='Portable acoustic, blackout, staging, storage.', start_date=date(2026, 2, 1), end_date=date(2026, 4, 30), created_by_id=coordinator_id),
        RoadmapItem(phase='phase_i', title='First annual review and report', year=2027, owner='Director', status='planned', details='Comprehensive assessment of Phase I activities, outputs, and governance.', start_date=date(2027, 10, 1), end_date=date(2027, 12, 31), created_by_id=director_id),
        RoadmapItem(phase='phase_ii', title='Secure successor site', year=2028, owner='Steering Group', status='planned', details='Identify candidate host institutions and property options.', start_date=date(2028, 1, 1), end_date=date(2028, 9, 30), created_by_id=director_id),
        RoadmapItem(phase='phase_ii', title='Build national artistic research network', year=2029, owner='Partnership Lead', status='planned', details='LMTA, VDA, research council, independent partners.', start_date=date(2029, 1, 1), end_date=date(2029, 12, 31), created_by_id=coordinator_id),
        RoadmapItem(phase='phase_ii', title='Transfer equipment and protocol to next platform', year=2029, owner='Technical Manager', status='planned', details='Move mobile kit, archive, and policy base to successor site.', start_date=date(2029, 6, 1), end_date=date(2030, 3, 31), created_by_id=admin_id),
    ])

    # ── Protocol ──
    db.session.add_all([
        ProtocolRule(principle='Spatial Flexibility', description='Each room must support research, seminar, and dissemination modes with minimal reconfiguration effort.', implementation='Use modular staging, acoustic panels, stackable seminar furniture, and blackout systems.', created_by_id=coordinator_id),
        ProtocolRule(principle='Research-First Scheduling', description='Scheduling must prioritize research processes over event-driven revenue logic.', implementation='Reserve weekday daytime and approved intensive blocks for research use only.', created_by_id=director_id),
        ProtocolRule(principle='Documentation Culture', description='Every supported project produces an auditable trail of process, reflection, and outputs.', implementation='Session logs, recordings, annotated notes, and monthly reports.', created_by_id=coordinator_id),
        ProtocolRule(principle='Portable Infrastructure', description='Investments must survive demolition through mobility and transfer planning.', implementation='Maintain inventory with owner, portability, and successor destination.', created_by_id=admin_id),
        ProtocolRule(principle='Governance Transparency', description='Roles, decisions, and risks must be visible to all partners.', implementation='Publish meeting records, reports, policies, and risk register on the platform.', created_by_id=director_id),
    ])

    # ── Constitution documents ──
    db.session.add_all([
        ConstitutionDocument(title='Kompresorinė Manifesto', category='manifesto', version='1.0', status='active',
            effective_date=date(2026, 1, 1),
            content='Kompresorinė is a temporary artistic research satellite. We operate on borrowed time, borrowed space, and provisional legitimacy — and we believe that temporary can be generative. We are not a venue. We are not an event producer. We are a site where artistic research is practiced seriously, documented rigorously, and shared critically. Our governance is not administrative overhead — it is an ethical commitment to the institutions, artists, and publics we serve.',
            created_by_id=director_id),
        ConstitutionDocument(title='Governance Constitution v1.0', category='constitution', version='1.0', status='active',
            effective_date=date(2026, 1, 15),
            content='This document establishes the governance structure of Kompresorinė for Phase I (2026–2028). Authority is shared between MTA (institutional anchor and partnership) and Ideas Block (operational management). Decisions affecting research priorities, budgets over €5,000, and Phase II planning require steering group approval. Day-to-day operational decisions rest with the coordinator.',
            created_by_id=director_id),
        ConstitutionDocument(title='Core Research Values', category='values', version='1.0', status='active',
            effective_date=date(2026, 1, 15),
            content='1. Research-first: artistic research is not content production. 2. Process visibility: document failures as rigorously as outcomes. 3. Institutional honesty: govern transparently, audit openly, report truthfully. 4. Portable knowledge: build so that nothing is lost when the space closes. 5. Critical hospitality: welcome collaborators into a serious working environment, not a service space.',
            created_by_id=coordinator_id),
    ])

    # ── Events ──
    db.session.add_all([
        DisseminationEvent(title='Research Demonstration: Embodied Sonic Methods', event_date=date.today()+timedelta(days=14), format='Research Demonstration', audience='public + academic', linked_project='Embodied Sonic Methods Lab', location='Research Studio A', project_id=p1.id, notes='Annotated public sharing with post-event discussion.', created_by_id=researcher_id),
        DisseminationEvent(title='Protocol Colloquium', event_date=date.today()+timedelta(days=21), format='Seminar', audience='partner institutions', linked_project='Black Box for Artistic Research', location='Seminar Zone', project_id=p2.id, notes='Invite LMTA, VDA, independent partners.', created_by_id=coordinator_id),
        DisseminationEvent(title='Open Studio Day', event_date=date.today()+timedelta(days=35), format='Open Studio', audience='general public', location='All spaces', notes='Kompresorinė opens its doors to the public.', created_by_id=admin_id),
    ])

    # ── Milestones ──
    db.session.flush()
    ms1 = Milestone(title='Complete first listening session cycle', project_id=p1.id, target_date=date.today()+timedelta(days=20), status='in_progress', created_by_id=researcher_id)
    ms2 = Milestone(title='Produce working paper draft', project_id=p1.id, target_date=date.today()+timedelta(days=60), status='pending', created_by_id=researcher_id)
    ms3 = Milestone(title='Test 3 spatial configurations', project_id=p2.id, target_date=date.today()+timedelta(days=10), status='reached', created_by_id=coordinator_id)
    ms4 = Milestone(title='Complete protocol handbook v1', project_id=p2.id, target_date=date.today()+timedelta(days=45), status='in_progress', created_by_id=coordinator_id)
    db.session.add_all([ms1, ms2, ms3, ms4])
    db.session.flush()

    # ── Tasks ──
    db.session.add_all([
        Task(title='Record second listening session', status='todo', priority='high', due_date=date.today()+timedelta(days=5), assigned_to_id=researcher_id, entity_type='projects', entity_id=p1.id, milestone_id=ms1.id, created_by_id=researcher_id),
        Task(title='Write session log for rehearsal 3', status='todo', priority='normal', due_date=date.today()+timedelta(days=7), assigned_to_id=researcher_id, entity_type='projects', entity_id=p1.id, created_by_id=researcher_id),
        Task(title='Book Seminar Zone for Protocol Colloquium', status='done', priority='normal', due_date=date.today()-timedelta(days=2), assigned_to_id=coordinator_id, entity_type='projects', entity_id=p2.id, created_by_id=coordinator_id),
        Task(title='Draft acoustic test report', status='todo', priority='high', due_date=date.today()+timedelta(days=3), assigned_to_id=coordinator_id, entity_type='projects', entity_id=p2.id, milestone_id=ms4.id, created_by_id=coordinator_id),
        Task(title='Update equipment transfer plan', status='todo', priority='normal', due_date=date.today()+timedelta(days=14), assigned_to_id=admin_id, entity_type='equipment', entity_id=1, created_by_id=admin_id),
    ])

    # ── Research sessions ──
    db.session.add_all([
        ResearchSession(project_id=p1.id, session_date=date.today()-timedelta(days=25), facilitator='Artist Researcher', participants='Artist Researcher, Research Coordinator', methods_used='Listening session, body-mapping', observations='Initial somatic responses to layered field recordings; participants noted spatial disorientation as generative.', open_questions='Can disorientation be structured? Is there a repeatable method here?', created_by_id=researcher_id),
        ResearchSession(project_id=p1.id, session_date=date.today()-timedelta(days=18), facilitator='Artist Researcher', participants='Artist Researcher, external collaborator', methods_used='Score-based performance, annotation', observations='Second iteration with graphic score. Score helped direct attention but constrained spontaneity.', open_questions='Score as constraint vs. score as map — test both approaches.', created_by_id=researcher_id),
        ResearchSession(project_id=p2.id, session_date=date.today()-timedelta(days=12), facilitator='Research Coordinator', participants='Research Coordinator, Admin User', methods_used='Spatial protocol testing, governance review', observations='Blackout system and acoustic panels tested with 3 different room configurations. Config C most effective for seminar mode.', open_questions='Does config C scale to larger groups? Test with 20+ participants.', created_by_id=coordinator_id),
    ])

    # ── Proposals ──
    db.session.add_all([
        ProposalRecord(meeting_id=m1.id, proposal_text='Approve pilot governance framework and designate weekday 9:00–17:00 blocks as protected research time requiring coordinator approval to override.', proposer='MC Director', outcome='approved', votes_for=4, votes_against=0, dissenting_notes='', created_by_id=director_id),
        ProposalRecord(meeting_id=m1.id, proposal_text='Allocate separate budget lines for research activities vs. public programming to enable per-project cost tracking.', proposer='Admin User', outcome='approved', votes_for=3, votes_against=1, dissenting_notes='One member noted this adds administrative overhead; recommended quarterly rather than monthly reconciliation.', created_by_id=admin_id),
        ProposalRecord(meeting_id=m2.id, proposal_text='Mandate session logs for all supported projects — minimum one log entry per residency cycle.', proposer='Research Coordinator', outcome='approved', votes_for=4, votes_against=0, dissenting_notes='', created_by_id=coordinator_id),
        ProposalRecord(meeting_id=m2.id, proposal_text='Expand public programming to three evenings per week to increase revenue.', proposer='Admin User', outcome='rejected', votes_for=1, votes_against=3, dissenting_notes='Majority view: this directly conflicts with Research-First Scheduling Protocol and would displace ongoing residencies. Alternative: cap public events at one evening per week.', created_by_id=admin_id),
    ])

    # ── Polls ──
    poll1 = Poll(title='Research-First Policy: Should we formalize the 9–17 weekday research block?', description='This vote will determine whether to codify weekday 9–17 as constitutionally protected research time, requiring written coordinator approval for any override.', poll_type='single', status='open', is_public=False, public_token=None, created_by_id=director_id)
    poll2 = Poll(title='Phase II Strategy: Which model should we pursue?', description='The steering group is evaluating three models for Phase II institutional development. Your vote will inform the partnership strategy.', poll_type='single', status='open', is_public=True, public_token=str(uuid.uuid4()).replace('-', ''), created_by_id=director_id)
    db.session.add_all([poll1, poll2])
    db.session.flush()

    opt1a = PollOption(poll_id=poll1.id, option_text='Yes — codify in the constitution with no exceptions')
    opt1b = PollOption(poll_id=poll1.id, option_text='Yes — codify but allow emergency overrides with documentation')
    opt1c = PollOption(poll_id=poll1.id, option_text='No — keep as a policy recommendation, not a constitutional rule')
    opt2a = PollOption(poll_id=poll2.id, option_text='Single successor site (one institution hosts the next Kompresorinė)')
    opt2b = PollOption(poll_id=poll2.id, option_text='Distributed network (multiple partner institutions, shared governance)')
    opt2c = PollOption(poll_id=poll2.id, option_text='Nomadic model (rotating host every 2–3 years)')
    db.session.add_all([opt1a, opt1b, opt1c, opt2a, opt2b, opt2c])
    db.session.flush()

    # Seed some votes
    db.session.add_all([
        PollVote(poll_id=poll1.id, option_id=opt1b.id, user_id=director_id),
        PollVote(poll_id=poll1.id, option_id=opt1b.id, user_id=coordinator_id),
        PollVote(poll_id=poll1.id, option_id=opt1a.id, user_id=admin_id),
    ])

    # ── Legacy Planning Tasks ──
    db.session.add_all([
        LegacyTask(category='equipment', title='Document transfer plan for all portable audio equipment', owner='Admin User', deadline=date(2027, 12, 1), status='in_progress', priority='high', description='Each portable audio item must have a named receiving institution and signed transfer agreement before Phase I closes.', notes='8 of 14 items assigned. Waiting on LMTA sign-off for the binaural rigs.', created_by_id=admin_id),
        LegacyTask(category='equipment', title='Photograph and catalogue all equipment for Phase II inventory', owner='Research Coordinator', deadline=date(2027, 10, 1), status='pending', priority='normal', description='Create a permanent photographic and descriptive record of all equipment regardless of transfer destination.', created_by_id=coordinator_id),
        LegacyTask(category='knowledge', title='Produce methods documentation for somatic listening research', owner='Artist Researcher', deadline=date(2028, 1, 1), status='pending', priority='urgent', description='The listening-score method developed in Project 1 is undocumented outside session logs. Needs a formal methodology document for Phase II researchers to build on.', created_by_id=researcher_id),
        LegacyTask(category='knowledge', title='Archive all session recordings and transcripts to institutional repository', owner='Research Coordinator', deadline=date(2028, 3, 1), status='pending', priority='high', description='All audio, video, and text records from research sessions must be transferred to an institutional repository with consistent metadata.', created_by_id=coordinator_id),
        LegacyTask(category='knowledge', title='Write Phase I retrospective report', owner='MC Director', deadline=date(2028, 6, 1), status='pending', priority='urgent', description='A comprehensive narrative and data-based account of Phase I: what was attempted, what succeeded, what failed, and what Phase II should carry forward.', created_by_id=director_id),
        LegacyTask(category='partnership', title='Formalise renewal intention with LMTA Mokslo centras', owner='MC Director', deadline=date(2027, 9, 1), status='in_progress', priority='urgent', description='The core partnership agreement expires at Phase I close. A renewal MOU must be signed or the partnership formally concluded with a transition plan.', notes='Negotiation meeting scheduled for April 2027.', created_by_id=director_id),
        LegacyTask(category='partnership', title='Document intellectual contributions of all partner institutions', owner='Research Coordinator', deadline=date(2027, 12, 1), status='pending', priority='normal', description='Create a structured record of co-authored outputs, shared methods, and intellectual debts to each partner — required for attribution in Phase II publications.', created_by_id=coordinator_id),
        LegacyTask(category='funding', title='Reconcile and close all Phase I budget lines', owner='Admin User', deadline=date(2028, 7, 1), status='pending', priority='high', description='Full financial reconciliation and closure of all grants, project budgets, and operational accounts before Phase II application.', created_by_id=admin_id),
        LegacyTask(category='funding', title='Prepare Phase II funding application', owner='MC Director', deadline=date(2027, 11, 1), status='pending', priority='urgent', description='The Phase II funding application must be submitted 6 months before Phase I closes. Requires retrospective evidence from the platform.', created_by_id=director_id),
        LegacyTask(category='governance', title='Archive meeting minutes and decision records in public repository', owner='Admin User', deadline=date(2028, 5, 1), status='pending', priority='normal', description='All governance records must be archived in a publicly accessible format — both for transparency and as a research output demonstrating governance methodology.', created_by_id=admin_id),
        LegacyTask(category='governance', title='Ratify Phase II governance constitution', owner='MC Director', deadline=date(2027, 8, 1), status='pending', priority='urgent', description='Phase II will operate with a different institutional structure. The governance model must be constitutionally ratified before the transition.', created_by_id=director_id),
        LegacyTask(category='research', title='Complete outputs documentation for all active research projects', owner='Research Coordinator', deadline=date(2028, 4, 1), status='pending', priority='high', description='Every project must have documented outputs — publications, scores, performances, prototypes — before the platform is archived.', created_by_id=coordinator_id),
        LegacyTask(category='research', title='Publish pilot research methodology as open-access document', owner='Artist Researcher', deadline=date(2028, 6, 1), status='pending', priority='normal', description='The research methods developed at Kompresorinė should be published as an open-access document, making the platform itself a research contribution.', created_by_id=researcher_id),
    ])

    db.session.commit()
    # Seed calls as separate step (also runs for existing DBs)
    _seed_calls(admin_id, coordinator_id)


