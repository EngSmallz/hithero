"""Seed immutable read fixtures used by SvelteKit SSR Playwright tests."""

import datetime
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)

import app
from backend.db.models import Spotlight


def main():
    app.Base.metadata.drop_all(bind=app.engine)
    app.Base.metadata.create_all(bind=app.engine)
    db = app.SessionLocal()
    try:
        teacher_user = app.RegisteredUsers(
            id=12,
            email="teacher@example.test",
            phone_number="555-0112",
            password=app.sha256_crypt.hash("test-password"),
            role="teacher",
            createCount=1,
        )
        random_user = app.RegisteredUsers(
            id=13,
            email="random@example.test",
            phone_number="555-0113",
            password=app.sha256_crypt.hash("test-password"),
            role="teacher",
            createCount=1,
        )
        db.add_all([teacher_user, random_user])
        db.add(
            app.TeacherList(
                name="Avery Adams",
                state="Washington",
                county="King",
                district="Seattle Public Schools",
                school="Evergreen Elementary",
                regUserID=12,
                wishlist_url="https://example.com/wishlist",
                about_me="I build a classroom where students can practice curiosity every day.",
                url_id="avery-adams",
            )
        )
        db.add(
            app.TeacherList(
                name="Random Riley",
                state="Washington",
                county="King",
                district="Seattle Public Schools",
                school="Random Elementary",
                regUserID=13,
                wishlist_url="https://example.com/random-wishlist",
                about_me="Random Riley supports curious classrooms.",
                url_id="random-riley",
            )
        )
        db.add(
            Spotlight(
                token="teacher",
                name="Avery Adams",
                state="Washington",
                county="King",
                district="Seattle Public Schools",
                school="Evergreen Elementary",
                image_data=None,
            )
        )
        db.add_all(
            [
                app.ForumPost(
                    id=101,
                    title="<strong>Newest</strong> discussion",
                    content=(
                        "<p>This discussion was rendered from a "
                        "<em>mocked forum API response</em>.</p>"
                        '<p><a href="https://example.test/supplies">'
                        "Safe classroom link</a></p>"
                    ),
                    created_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
                    user_id=7,
                    upvote_count=3,
                    comment_count=2,
                ),
                app.ForumPost(
                    id=102,
                    title="Older highly voted discussion",
                    content="A discussion with more upvotes for sorting coverage.",
                    created_at=datetime.datetime(2026, 5, 10, 12, 0, 0),
                    user_id=8,
                    upvote_count=12,
                    comment_count=0,
                ),
                app.ForumPost(
                    id=103,
                    title="Oldest discussion",
                    content="The oldest classroom discussion in this mocked list.",
                    created_at=datetime.datetime(2026, 4, 10, 12, 0, 0),
                    user_id=9,
                    upvote_count=1,
                    comment_count=4,
                ),
                *[
                    app.ForumPost(
                        id=104 + index,
                        title=f"Additional discussion {index + 1}",
                        content=f"Additional pagination fixture {index + 1}.",
                        created_at=datetime.datetime(2026, 5, index + 1, 12, 0, 0),
                        user_id=9,
                        upvote_count=index + 2,
                        comment_count=0,
                    )
                    for index in range(9)
                ],
            ]
        )
        db.add_all(
            [
                app.ForumComment(
                    id=201,
                    post_id=101,
                    user_id=8,
                    content="This comment was loaded from the <strong>comments endpoint</strong>.",
                    created_at=datetime.datetime(2026, 6, 11, 12, 0, 0),
                ),
                app.ForumComment(
                    id=202,
                    post_id=101,
                    user_id=9,
                    content="A second read-only comment.",
                    created_at=datetime.datetime(2026, 6, 12, 12, 0, 0),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
