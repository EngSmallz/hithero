"""Teacher selection logic: random teacher and Teacher of the Day."""
import datetime
from sqlalchemy import func
from sqlalchemy.sql import select

from app.database import SessionLocal
from app.models import TeacherList

# Function to fetch a random teacher from the database
def fetch_random_teacher():
    db = SessionLocal()
    try:
        # The scalar_one_or_none() method directly returns the TeacherList object,
        # or None if no teacher is found.
        query = select(TeacherList).order_by(func.newid()).limit(1)
        random_teacher_record = db.execute(query).scalar_one_or_none()
        return random_teacher_record
    except Exception as e:
        print(f"Error fetching random teacher: {e}")
        return None
    finally:
        db.close()

def fetch_teacher_for_tod():
    """
    Picks the next Teacher of the Day: a random teacher not featured in the
    last 90 days (or never featured). If everyone was featured within 90
    days, the teacher featured longest ago. None only when there are no
    teachers. Does not change any data; the caller stamps last_TOD.

    This used to loop "while True" over random picks, which never returned
    once every teacher had been featured recently and hung the daily job.
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    db = SessionLocal()
    try:
        eligible = select(TeacherList).where(
            (TeacherList.last_TOD.is_(None)) | (TeacherList.last_TOD < cutoff)
        ).order_by(func.newid()).limit(1)
        teacher = db.execute(eligible).scalar_one_or_none()
        if teacher is None:
            oldest = select(TeacherList).order_by(TeacherList.last_TOD).limit(1)
            teacher = db.execute(oldest).scalar_one_or_none()
        return teacher
    finally:
        db.close()
