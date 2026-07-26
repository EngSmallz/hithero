from __future__ import annotations

import argparse
import datetime
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


def seed_password_reset_token(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        db.add(
            app_module.PasswordResetToken(
                email=args.email,
                token=args.token,
                expires_at=datetime.datetime.utcnow()
                + datetime.timedelta(hours=args.expires_in_hours),
                used=args.used,
            )
        )


def seed_teacher_profile(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = (
            db.query(app_module.RegisteredUsers)
            .filter(app_module.RegisteredUsers.email == args.email)
            .one_or_none()
        )

        if user is None:
            raise SystemExit(f"Registered user not found: {args.email}")

        db.add(
            app_module.TeacherList(
                name=args.name,
                state=args.state,
                county=args.county,
                district=args.district,
                school=args.school,
                regUserID=user.id,
                wishlist_url=args.wishlist_url,
                about_me=args.about_me,
                url_id=args.url_id,
            )
        )


def seed_forum_post(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = (
            db.query(app_module.RegisteredUsers)
            .filter(app_module.RegisteredUsers.email == args.email)
            .one_or_none()
        )

        if user is None:
            raise SystemExit(f"Registered user not found: {args.email}")

        db.add(
            app_module.ForumPost(
                title=args.title,
                content=args.content,
                user_id=user.id,
                created_at=datetime.datetime.fromisoformat(args.created_at),
                upvote_count=args.upvote_count,
                comment_count=args.comment_count,
            )
        )


def seed_forum_comment(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = (
            db.query(app_module.RegisteredUsers)
            .filter(app_module.RegisteredUsers.email == args.email)
            .one_or_none()
        )
        post = (
            db.query(app_module.ForumPost)
            .filter(app_module.ForumPost.title == args.post_title)
            .one_or_none()
        )

        if user is None:
            raise SystemExit(f"Registered user not found: {args.email}")
        if post is None:
            raise SystemExit(f"Forum post not found: {args.post_title}")

        db.add(
            app_module.ForumComment(
                content=args.content,
                post_id=post.id,
                user_id=user.id,
                created_at=datetime.datetime.fromisoformat(args.created_at),
            )
        )


def get_forum_post(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        post = (
            db.query(app_module.ForumPost)
            .filter(app_module.ForumPost.title == args.title)
            .one_or_none()
        )

        if post is None:
            print("null")
            return

        print(
            json.dumps(
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "user_id": post.user_id,
                    "upvote_count": post.upvote_count,
                    "comment_count": post.comment_count,
                },
                sort_keys=True,
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


def get_registered_user(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = (
            db.query(app_module.RegisteredUsers)
            .filter(app_module.RegisteredUsers.email == args.email)
            .one_or_none()
        )

        if user is None:
            print("null")
            return

        print(
            json.dumps(
                {
                    "email": user.email,
                    "create_count": user.createCount,
                    "password_is_hashed": user.password != args.plain_password,
                    "password_matches": app_module.sha256_crypt.verify(
                        args.plain_password, user.password
                    ),
                },
                sort_keys=True,
            )
        )


def get_teacher_profile(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        user = (
            db.query(app_module.RegisteredUsers)
            .filter(app_module.RegisteredUsers.email == args.email)
            .one_or_none()
        )

        if user is None:
            print("null")
            return

        teacher = (
            db.query(app_module.TeacherList)
            .filter(app_module.TeacherList.regUserID == user.id)
            .one_or_none()
        )

        if teacher is None:
            print("null")
            return

        print(
            json.dumps(
                {
                    "name": teacher.name,
                    "state": teacher.state,
                    "county": teacher.county,
                    "district": teacher.district,
                    "school": teacher.school,
                    "reg_user_id": teacher.regUserID,
                    "wishlist_url": teacher.wishlist_url,
                    "about_me": teacher.about_me,
                    "url_id_present": bool(teacher.url_id),
                },
                sort_keys=True,
            )
        )


def get_password_reset_token(args: argparse.Namespace) -> None:
    app_module = load_app()
    with session_scope(app_module) as db:
        token = (
            db.query(app_module.PasswordResetToken)
            .filter(app_module.PasswordResetToken.email == args.email)
            .order_by(app_module.PasswordResetToken.id.desc())
            .first()
        )

        if token is None:
            print("null")
            return

        print(
            json.dumps(
                {
                    "email": token.email,
                    "token_present": bool(token.token),
                    "used": token.used,
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

    seed_password_reset_token_parser = subparsers.add_parser("seed-password-reset-token")
    seed_password_reset_token_parser.add_argument("--email", required=True)
    seed_password_reset_token_parser.add_argument("--token", required=True)
    seed_password_reset_token_parser.add_argument("--expires-in-hours", type=int, default=1)
    seed_password_reset_token_parser.add_argument("--used", type=int, default=0)
    seed_password_reset_token_parser.set_defaults(func=seed_password_reset_token)

    seed_teacher_profile_parser = subparsers.add_parser("seed-teacher-profile")
    seed_teacher_profile_parser.add_argument("--email", required=True)
    seed_teacher_profile_parser.add_argument("--name", required=True)
    seed_teacher_profile_parser.add_argument("--state", required=True)
    seed_teacher_profile_parser.add_argument("--county", required=True)
    seed_teacher_profile_parser.add_argument("--district", required=True)
    seed_teacher_profile_parser.add_argument("--school", required=True)
    seed_teacher_profile_parser.add_argument("--wishlist-url", required=True)
    seed_teacher_profile_parser.add_argument("--about-me", required=True)
    seed_teacher_profile_parser.add_argument("--url-id", required=True)
    seed_teacher_profile_parser.set_defaults(func=seed_teacher_profile)

    seed_forum_post_parser = subparsers.add_parser("seed-forum-post")
    seed_forum_post_parser.add_argument("--email", required=True)
    seed_forum_post_parser.add_argument("--title", required=True)
    seed_forum_post_parser.add_argument("--content", required=True)
    seed_forum_post_parser.add_argument("--created-at", default="2026-06-10T12:00:00")
    seed_forum_post_parser.add_argument("--upvote-count", type=int, default=0)
    seed_forum_post_parser.add_argument("--comment-count", type=int, default=0)
    seed_forum_post_parser.set_defaults(func=seed_forum_post)

    seed_forum_comment_parser = subparsers.add_parser("seed-forum-comment")
    seed_forum_comment_parser.add_argument("--email", required=True)
    seed_forum_comment_parser.add_argument("--post-title", required=True)
    seed_forum_comment_parser.add_argument("--content", required=True)
    seed_forum_comment_parser.add_argument("--created-at", default="2026-06-11T12:00:00")
    seed_forum_comment_parser.set_defaults(func=seed_forum_comment)

    get_new_user_parser = subparsers.add_parser("get-new-user")
    get_new_user_parser.add_argument("--email", required=True)
    get_new_user_parser.add_argument("--plain-password", required=True)
    get_new_user_parser.set_defaults(func=get_new_user)

    get_registered_user_parser = subparsers.add_parser("get-registered-user")
    get_registered_user_parser.add_argument("--email", required=True)
    get_registered_user_parser.add_argument("--plain-password", required=True)
    get_registered_user_parser.set_defaults(func=get_registered_user)

    get_teacher_profile_parser = subparsers.add_parser("get-teacher-profile")
    get_teacher_profile_parser.add_argument("--email", required=True)
    get_teacher_profile_parser.set_defaults(func=get_teacher_profile)

    get_password_reset_token_parser = subparsers.add_parser("get-password-reset-token")
    get_password_reset_token_parser.add_argument("--email", required=True)
    get_password_reset_token_parser.set_defaults(func=get_password_reset_token)

    get_forum_post_parser = subparsers.add_parser("get-forum-post")
    get_forum_post_parser.add_argument("--title", required=True)
    get_forum_post_parser.set_defaults(func=get_forum_post)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
