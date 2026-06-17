from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")


def load_app():
    if not os.getenv("DATABASE_URL") and not os.getenv("TEST_DATABASE_URL"):
        raise SystemExit("DATABASE_URL or TEST_DATABASE_URL must point at an isolated test DB")

    import app

    return app


@contextmanager
def session_scope(app_module):
    db = app_module.SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_database(args: argparse.Namespace) -> None:
    app_module = load_app()
    app_module.Base.metadata.drop_all(bind=app_module.engine)
    app_module.Base.metadata.create_all(bind=app_module.engine)


def seed_login_user(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        db.add(
            app_module.RegisteredUsers(
                email=args.email,
                phone_number=args.phone_number,
                password=app_module.sha256_crypt.hash(args.password),
                role=args.role,
                createCount=args.create_count,
            )
        )


def seed_school(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        db.add(
            app_module.School(
                state=args.state,
                county=args.county,
                district=args.district,
                school_name=args.school,
            )
        )


def get_new_user(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = db.query(app_module.NewUsers).filter(app_module.NewUsers.email == args.email).one_or_none()

        if user is None:
            print("null")
            return

        print(
            json.dumps(
                {
                    "email": user.email,
                    "name": user.name,
                    "phone_number": user.phone_number,
                    "state": user.state,
                    "county": user.county,
                    "district": user.district,
                    "school": user.school,
                    "role": user.role,
                    "report": user.report,
                    "emailed": user.emailed,
                    "password_is_hashed": user.password != args.plain_password,
                },
                sort_keys=True,
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Integration test DB helper")
    subparsers = parser.add_subparsers(required=True)

    reset_parser = subparsers.add_parser("reset")
    reset_parser.set_defaults(func=reset_database)

    seed_user_parser = subparsers.add_parser("seed-login-user")
    seed_user_parser.add_argument("--email", required=True)
    seed_user_parser.add_argument("--password", required=True)
    seed_user_parser.add_argument("--role", default="teacher")
    seed_user_parser.add_argument("--create-count", type=int, default=0)
    seed_user_parser.add_argument("--phone-number", default="555-0100")
    seed_user_parser.set_defaults(func=seed_login_user)

    seed_school_parser = subparsers.add_parser("seed-school")
    seed_school_parser.add_argument("--state", required=True)
    seed_school_parser.add_argument("--county", required=True)
    seed_school_parser.add_argument("--district", required=True)
    seed_school_parser.add_argument("--school", required=True)
    seed_school_parser.set_defaults(func=seed_school)

    get_new_user_parser = subparsers.add_parser("get-new-user")
    get_new_user_parser.add_argument("--email", required=True)
    get_new_user_parser.add_argument("--plain-password", required=True)
    get_new_user_parser.set_defaults(func=get_new_user)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
