from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import (
    User, Track, Enrollment, MentorAssignment, Task, TaskAssignment, TaskProgress,
    Meeting, MeetingAttendee, Announcement, LearningResource, DemoProduct, SystemSetting,
    Notification
)
from .security import hash_password, verify_password

SUPER_EMAIL = "superadmin@hvia.ai"
SUPER_PASSWORD = "HVIA@SuperAdmin#2026!"
ADMIN_EMAIL = "admin@hvia.ai"
ADMIN_PASSWORD = "HVIA@Admin#2026!"
MENTOR_EMAIL = "mentor@hvia.ai"
MENTOR_PASSWORD = "HVIA@Mentor#2026!"

INTERNS = [
    ("A’laa Ashraf", "ea8284473@gmail.com", "alaa.ashraf@hvia.ai", "Hv!A26-gQP4yXp"),
    ("Aalaa Aboelazm", "aalaaaboelazm@gmail.com", "aalaa.aboelazm@hvia.ai", "Hv!A26-qLuo66i"),
    ("Abdelrahman Shalaby", "abdelrahmanshalaby24@gmail.com", "abdelrahman.shalaby@hvia.ai", "Hv!A26-xpiQL6A"),
    ("Abdullah EmadEldin", "abdullahemadeldin28@gmail.com", "abdullah.emadeldin@hvia.ai", "Hv!A26-EuUrtxm"),
    ("ahmad elsherif", "ahmad.elsherriff@gmail.com", "ahmad.elsherif@hvia.ai", "Hv!A26-u8VoFse"),
    ("Ahmed Akram", "ahmedakram3ai@gmail.com", "ahmed.akram@hvia.ai", "Hv!A26-FE4UWVC"),
    ("ahmed fwaz", "ahmedfwaz2007@gmail.com", "ahmed.fwaz@hvia.ai", "Hv!A26-xQ98Pnl"),
    ("AHMED Hossam", "ahmedhossamfoda@gmail.com", "ahmed.hossam@hvia.ai", "Hv!A26-MLLYmxj"),
    ("Ahmed Saad", "ahmedskaram2@gmail.com", "ahmed.saad@hvia.ai", "Hv!A26-9zmpgTx"),
    ("Ahmed tarek", "ahmed46828e@gmail.com", "ahmed.tarek@hvia.ai", "Hv!A26-imQHwtb"),
]


def ensure_user(db: Session, *, internal_id: str, full_name: str, email: str, password: str, role: str, personal_email=None, profile_completed=True):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(
            internal_id=internal_id,
            full_name=full_name,
            email=email,
            personal_email=personal_email,
            password_hash=hash_password(password),
            role=role,
            active=True,
            status="active",
            profile_completed=profile_completed,
        )
        db.add(u)
        db.flush()
    else:
        u.role = role
        u.active = True
        u.status = "active"
        if not u.password_hash or not verify_password(password, u.password_hash):
            u.password_hash = hash_password(password)
        db.flush()
    return u


def ensure_track(db: Session, name: str, program_type: str, description: str):
    t = db.query(Track).filter(Track.name == name).first()
    if not t:
        t = Track(name=name, program_type=program_type, description=description, active=True, capacity=500)
        db.add(t)
        db.flush()
    return t


def add_attendees_for_meeting(db, meeting):
    if db.query(MeetingAttendee).filter(MeetingAttendee.meeting_id == meeting.id).count():
        return
    q = db.query(User).filter(User.active == True, User.deleted_at.is_(None))
    if meeting.target_type == "admins":
        q = q.filter(User.role == "admin")
    elif meeting.target_type == "interns":
        q = q.filter(User.role == "intern")
    elif meeting.target_type == "specific" and meeting.target_user_id:
        q = q.filter(User.id == meeting.target_user_id)
    elif meeting.target_type == "track" and meeting.target_track_id:
        ids = [e.user_id for e in db.query(Enrollment).filter(Enrollment.track_id == meeting.target_track_id, Enrollment.active == True).all()]
        q = q.filter(User.id.in_(ids or [-1]))
    for user in q.all():
        db.add(MeetingAttendee(meeting_id=meeting.id, user_id=user.id, attendance_status="invited"))


def seed_database(db: Session):
    tracks = [
        ensure_track(db, "Data Analysis", "internship", "Excel, SQL, Python, Power BI, Tableau and real business analytics projects."),
        ensure_track(db, "AI & Machine Learning", "internship", "Python, machine learning, model development, evaluation and applied projects."),
        ensure_track(db, "Bootcamp - Data Analysis", "bootcamp", "Structured bootcamp with modules, protected learning content, books and assignments."),
    ]

    super_admin = ensure_user(db, internal_id="HVIA-SADM-2026-001", full_name="Ayman Abdelnasser", email=SUPER_EMAIL, password=SUPER_PASSWORD, role="super_admin")
    admin = ensure_user(db, internal_id="HVIA-ADM-2026-001", full_name="HVIA Internship Admin", email=ADMIN_EMAIL, password=ADMIN_PASSWORD, role="admin")
    mentor = ensure_user(db, internal_id="HVIA-ADM-2026-002", full_name="HVIA Mentor", email=MENTOR_EMAIL, password=MENTOR_PASSWORD, role="admin")

    intern_users = []
    for idx, (name, personal, company, password) in enumerate(INTERNS, 1):
        u = db.query(User).filter(User.email == company).first()
        if not u:
            u = User(
                internal_id=f"HVIA-INT-2026-{idx:04d}", full_name=name, email=company,
                personal_email=personal, password_hash=hash_password(password), role="intern",
                active=True, status="onboarding", profile_completed=False,
            )
            db.add(u); db.flush()
        intern_users.append(u)
        if not db.query(Enrollment).filter(Enrollment.user_id == u.id, Enrollment.active == True).first():
            db.add(Enrollment(user_id=u.id, track_id=None, status="pending", active=True))

    db.flush()
    for i, intern in enumerate(intern_users):
        assigned_admin = admin if i < 5 else mentor
        if not db.query(MentorAssignment).filter(MentorAssignment.admin_id == assigned_admin.id, MentorAssignment.intern_id == intern.id, MentorAssignment.active == True).first():
            db.add(MentorAssignment(admin_id=assigned_admin.id, intern_id=intern.id, assigned_by=super_admin.id, active=True))

    now = datetime.utcnow()
    if db.query(Task).count() == 0:
        demo_tasks = [
            Task(title="EDA Project Report", description="Analyze the provided business dataset and submit your notebook/report.", instructions="Submit notebook, PDF, Word, ZIP or any supporting file. Any file type is accepted.", created_by=admin.id, target_type="track", target_track_id=tracks[0].id, priority="High", deadline=now+timedelta(days=7), max_score=100),
            Task(title="ML Model Presentation", description="Build a baseline ML model and document the evaluation.", instructions="You may submit notebook, source files, PDF, slides, ZIP or links.", created_by=mentor.id, target_type="track", target_track_id=tracks[1].id, priority="High", deadline=now+timedelta(days=10), max_score=100),
            Task(title="Bootcamp Practice Assignment", description="Complete Module 1 exercises and submit your solution.", created_by=admin.id, target_type="track", target_track_id=tracks[2].id, priority="Medium", deadline=now+timedelta(days=5), max_score=100),
        ]
        db.add_all(demo_tasks); db.flush()

    if db.query(Meeting).count() == 0:
        meetings = [
            Meeting(title="HVIA Internship Kickoff", description="Program overview, rules and workflow.", starts_at=now+timedelta(days=2), duration_minutes=60, meeting_link="https://meet.google.com/", target_type="interns", created_by=super_admin.id),
            Meeting(title="Mentor Operations Sync", description="Super Admin meeting with all mentors/admins.", starts_at=now+timedelta(days=3), duration_minutes=45, meeting_link="https://meet.google.com/", target_type="admins", created_by=super_admin.id),
        ]
        db.add_all(meetings); db.flush()
        for m in meetings: add_attendees_for_meeting(db, m)

    if db.query(Announcement).count() == 0:
        db.add(Announcement(title="Welcome to HVIA Internship 2026", content="Complete your profile, choose your track, then check Tasks, Meetings and Notifications.", target_type="all", created_by=super_admin.id, pinned=True))

    if db.query(LearningResource).count() == 0:
        db.add_all([
            LearningResource(track_id=tracks[2].id, title="Python Fundamentals - Lesson 1", resource_type="video", url="/demo-video", description="Demo protected lesson placeholder.", module_name="Module 1 - Python", order_index=1, created_by=admin.id),
            LearningResource(track_id=tracks[2].id, title="Python Quick Reference", resource_type="book", url="/demo-book", description="Reference handbook.", module_name="Module 1 - Python", order_index=2, created_by=admin.id),
        ])

    if db.query(DemoProduct).count() == 0:
        db.add_all([
            DemoProduct(name="Retail Intelligence", category="Data & Analytics", description="Sales, inventory, forecasting and executive dashboards for retail businesses.", demo_url="#", image_url="/assets/generated/demo-analytics.png"),
            DemoProduct(name="Hospitality Intelligence", category="Business Intelligence", description="Revenue, occupancy, guest analytics and operational monitoring for hotels.", demo_url="#", image_url="/assets/generated/demo-dashboard.png"),
            DemoProduct(name="Manufacturing Intelligence", category="Operations", description="Production, quality, inventory and performance monitoring for manufacturing operations.", demo_url="#", image_url="/assets/generated/demo-platform.png"),
            DemoProduct(name="Custom Data Platform", category="Data Solutions", description="Custom dashboards and business systems designed around your workflow.", demo_url="#", image_url="/assets/generated/demo-solutions.png"),
        ])

    defaults = {
        "whatsapp_number": "201222970033",
        "company_name": "HVIA - Data & AI Solutions",
        "ceo_name": "Ayman Abdelnasser",
    }
    for key, value in defaults.items():
        if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
            db.add(SystemSetting(key=key, value=value, updated_by=super_admin.id))

    # Welcome notifications for admins
    for a in [admin, mentor]:
        if not db.query(Notification).filter(Notification.user_id == a.id, Notification.title == "HVIA Mentor Portal").first():
            db.add(Notification(user_id=a.id, title="HVIA Mentor Portal", message="Your mentor workspace is active. Tasks, reviews, meetings and assigned interns are available here.", notification_type="system"))

    db.commit()
