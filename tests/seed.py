"""Recreate the local test database and load seed data (BE1-3).

Run through scripts/test_db.sh, or directly with: python -m tests.seed

Drops and recreates the hithero_test database so ids are the same on
every run, builds the tables from app.py's models, then inserts:
  - schools in two states
  - 3 teachers, each with a login and a teacher page
  - 1 admin
  - 1 user waiting for validation
  - 2 forum posts with comments and votes

All seed logins use the password in SEED_PASSWORD.

Schema note: app.py's models cannot build an empty database as they
stand. password_reset_tokens.token is String with no length (VARCHAR(max))
and unique=True, and SQL Server cannot index VARCHAR(max) (error 1919).
So production's tables were not made by this create_all, and their real
column types are unknown until the BE2-1 audit. Here the token column is
given a length before the tables are built. Everything else matches the
models.
"""
import datetime
import os

from tests import testenv

SEED_PASSWORD = "Seed-Passw0rd!"

ADMIN_EMAIL = "admin@example.com"
TEACHER_EMAILS = ["alice@example.com", "bob@example.com", "carol@example.com"]
PENDING_EMAIL = "pending@example.com"


def recreate_database() -> None:
    import sqlalchemy

    env = {k: os.environ[k] for k in testenv.TEST_ENV}
    master = sqlalchemy.engine.URL.create(
        "mssql+pyodbc",
        username=env["DATABASE_UID"],
        password=env["DATABASE_PASSWORD"],
        host=env["DATABASE_SERVER"],
        port=int(env["DATABASE_PORT"]),
        database="master",
        query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
    )
    name = env["DATABASE_NAME"]
    if not name.replace("_", "").isalnum():
        raise SystemExit(f"Refusing odd database name: {name!r}")
    engine = sqlalchemy.create_engine(master, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.exec_driver_sql(
            f"IF DB_ID('{name}') IS NOT NULL BEGIN "
            f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
            f"DROP DATABASE [{name}]; END"
        )
        conn.exec_driver_sql(f"CREATE DATABASE [{name}]")
    engine.dispose()


def seed() -> None:
    from passlib.hash import sha256_crypt

    import sqlalchemy

    from app import database as app_module
    from app.models import (
        ForumComment,
        ForumPost,
        NewUsers,
        PasswordResetToken,
        PostVote,
        RegisteredUsers,
        School,
        TeacherList,
    )

    PasswordResetToken.__table__.c.token.type = sqlalchemy.String(255)
    app_module.engine.dispose()  # drop connections to the old database
    testenv.real_create_all(app_module.Base.metadata, bind=app_module.engine)

    # Low rounds keep seeding fast; verify() reads the rounds from the hash.
    password = sha256_crypt.using(rounds=1000, salt="seedsalt").hash(SEED_PASSWORD)

    schools = [
        ("Lincoln Elementary", "Springfield District", "Sangamon", "Illinois"),
        ("Douglas Middle", "Springfield District", "Sangamon", "Illinois"),
        ("Prairie High", "Champaign Unit 4", "Champaign", "Illinois"),
        ("Alamo Elementary", "San Antonio ISD", "Bexar", "Texas"),
    ]
    teachers = [
        # name, email, school index, url_id, about, last teacher-of-the-day
        ("Alice Adams", TEACHER_EMAILS[0], 0, "alice1234", "I teach 3rd grade.",
         datetime.datetime(2026, 1, 15, 8, 0)),
        ("Bob Brown", TEACHER_EMAILS[1], 0, "bob5678", "Art teacher.", None),
        ("Carol Cruz", TEACHER_EMAILS[2], 3, "carol42", "Science and robotics.", None),
    ]

    db = app_module.SessionLocal()
    try:
        for school_name, district, county, state in schools:
            db.add(School(school_name=school_name, district=district, county=county, state=state))

        admin = RegisteredUsers(email=ADMIN_EMAIL, phone_number="5550000000",
                                password=password, role="admin", createCount=0)
        db.add(admin)

        teacher_users = []
        for name, email, school_idx, url_id, about, last_tod in teachers:
            user = RegisteredUsers(email=email, phone_number="5550000001",
                                   password=password, role="teacher", createCount=1)
            db.add(user)
            db.flush()
            teacher_users.append(user)
            school_name, district, county, state = schools[school_idx]
            db.add(TeacherList(
                name=name, state=state, county=county, district=district,
                school=school_name, regUserID=user.id,
                wishlist_url=f"https://www.amazon.com/hz/wishlist/ls/{url_id.upper()}&tag=h0mer00mher0-20",
                about_me=about, image_data=None, url_id=url_id, last_TOD=last_tod,
            ))

        school_name, district, county, state = schools[1]
        db.add(NewUsers(name="Pat Pending", email=PENDING_EMAIL, state=state,
                        county=county, district=district, school=school_name,
                        phone_number="5550000002", password=password,
                        role="teacher", report=0, emailed=0))
        db.flush()

        alice, bob, carol = teacher_users
        created = datetime.datetime(2026, 2, 1, 12, 0)
        post1 = ForumPost(title="Classroom library ideas",
                          content="<p>What books do your students love?</p>",
                          user_id=alice.id, created_at=created,
                          upvote_count=2, comment_count=2)
        post2 = ForumPost(title="Fundraising tips",
                          content="<p>Share what worked for you.</p>",
                          user_id=carol.id, created_at=created + datetime.timedelta(days=1),
                          upvote_count=0, comment_count=1)
        db.add_all([post1, post2])
        db.flush()

        c1 = ForumComment(content="Graphic novels!", post_id=post1.id, user_id=bob.id,
                          created_at=created + datetime.timedelta(hours=1))
        db.add(c1)
        db.flush()
        db.add_all([
            ForumComment(content="Agreed, they fly off the shelf.", post_id=post1.id,
                         user_id=alice.id, parent_comment_id=c1.id,
                         created_at=created + datetime.timedelta(hours=2)),
            ForumComment(content="Local businesses sponsor us.", post_id=post2.id,
                         user_id=bob.id, created_at=created + datetime.timedelta(days=1, hours=1)),
            PostVote(post_id=post1.id, user_id=bob.id, vote_type=1),
            PostVote(post_id=post1.id, user_id=carol.id, vote_type=1),
        ])
        db.commit()
    finally:
        db.close()


def main() -> None:
    testenv.configure(force_database=True)
    recreate_database()
    seed()
    print("Seeded hithero_test.")


if __name__ == "__main__":
    main()
