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
    Picks the next Teacher of the Day.

    Repeatedly calls fetch_random_teacher() and checks the returned
    teacher's last_TOD against a 90-day cutoff, until it finds someone
    who either has never been featured (last_TOD is NULL) or wasn't
    featured in the last 90 days. Does not mutate any data - the caller
    is responsible for stamping last_TOD once the pick is finalized.
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    while True:
        candidate = fetch_random_teacher()
        if candidate is None:
            # No teachers at all in teacher_list.
            return None
        if candidate.last_TOD is None or candidate.last_TOD < cutoff:
            return candidate
        # Otherwise loop and try again - candidate was featured too recently.