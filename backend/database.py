import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/hvia_internship.db" if os.getenv("VERCEL") else "sqlite:///./data/hvia_internship.db")
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine_kwargs = {"pool_pre_ping": True, "connect_args": connect_args}
if not is_sqlite:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_recycle": 1800})
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_users_role_active ON users (role, active)",
    "CREATE INDEX IF NOT EXISTS ix_users_last_seen ON users (last_seen_at)",
    "CREATE INDEX IF NOT EXISTS ix_enrollments_track_active ON enrollments (track_id, active)",
    "CREATE INDEX IF NOT EXISTS ix_enrollments_user_active ON enrollments (user_id, active)",
    "CREATE INDEX IF NOT EXISTS ix_mentor_assignments_admin_active ON mentor_assignments (admin_id, active)",
    "CREATE INDEX IF NOT EXISTS ix_mentor_assignments_intern_active ON mentor_assignments (intern_id, active)",
    "CREATE INDEX IF NOT EXISTS ix_task_assignments_user_task ON task_assignments (user_id, task_id)",
    "CREATE INDEX IF NOT EXISTS ix_task_progress_user_status ON task_progress (user_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_submissions_user_status ON submissions (user_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_submissions_task_user ON submissions (task_id, user_id)",
    "CREATE INDEX IF NOT EXISTS ix_meeting_attendees_user_meeting ON meeting_attendees (user_id, meeting_id)",
    "CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications (user_id, is_read)",
    "CREATE INDEX IF NOT EXISTS ix_activity_created ON activity_log (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_login_events_email_created ON login_events (email_attempt, created_at)"
]

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for stmt in INDEXES:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
