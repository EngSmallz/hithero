from fastapi.testclient import TestClient
from sqlalchemy import delete


SAFE_CONTENT = (
    '<p>Hello <em data-extra="drop-me">teachers</em></p>'
    '<p><a href="https://example.test/path" onclick="alert(2)" style="color:red">'
    "Safe link</a></p>"
    '<a href="mailto:team@example.test">Email us</a>'
    '<a href="javascript:alert(1)">Unsafe link</a>'
    '<script>alert("nope")</script>'
    '<img src=x onerror=alert(3)>'
    '<span style="color:red">Span text</span>'
)


def seed_forum_user(app_module, *, email="forum-html-safety@example.test"):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.PostVote))
        db.execute(delete(app_module.ForumComment))
        db.execute(delete(app_module.ForumPost))
        db.execute(delete(app_module.RegisteredUsers))
        user = app_module.RegisteredUsers(
            email=email,
            phone_number="555-0100",
            password=app_module.sha256_crypt.hash("test-password"),
            role="teacher",
            createCount=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def login_forum_user(client, *, email="forum-html-safety@example.test"):
    response = client.post(
        "/profile/login/",
        data={
            "email": email,
            "password": "test-password",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "teacher"


def assert_forum_html_is_safe(value):
    lowered = value.lower()
    for unsafe in [
        "<script",
        "</script",
        "<img",
        "<span",
        "javascript:",
        "ftp://",
        "onclick",
        "onerror",
        "style=",
        "data-extra",
    ]:
        assert unsafe not in lowered


def create_forum_post(client, *, title="<strong>Classroom supplies</strong>", content=SAFE_CONTENT):
    response = client.post(
        "/forum/create_post",
        data={
            "title": title,
            "content": content,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_forum_html_allowlist_is_explicit(app_module):
    assert app_module.ALLOWED_TAGS == ["b", "i", "em", "strong", "a", "p", "br"]
    assert app_module.ALLOWED_ATTRS == {"a": ["href"]}
    assert app_module.ALLOWED_PROTOCOLS == ["http", "https", "mailto"]


def test_forum_post_creation_preserves_safe_html_and_strips_unsafe_markup(app_module):
    seed_forum_user(app_module)
    client = TestClient(app_module.app)
    login_forum_user(client)

    post = create_forum_post(client)

    assert post["title"] == "<strong>Classroom supplies</strong>"
    assert '<p>Hello <em>teachers</em></p>' in post["content"]
    assert '<a href="https://example.test/path">Safe link</a>' in post["content"]
    assert '<a href="mailto:team@example.test">Email us</a>' in post["content"]
    assert "<a>Unsafe link</a>" in post["content"]
    assert "Span text" in post["content"]
    assert_forum_html_is_safe(post["content"])

    db = app_module.SessionLocal()
    try:
        stored_post = db.query(app_module.ForumPost).one()
        assert stored_post.title == post["title"]
        assert stored_post.content == post["content"]
    finally:
        db.close()


def test_forum_post_creation_decodes_double_encoded_and_malformed_payloads(app_module):
    seed_forum_user(app_module)
    client = TestClient(app_module.app)
    login_forum_user(client)

    post = create_forum_post(
        client,
        title=(
            "&amp;lt;strong onclick=alert(1)&amp;gt;Encoded title"
            "&amp;lt;/strong&amp;gt;&amp;lt;img src=x onerror=alert(2)&amp;gt;"
        ),
        content=(
            "&amp;lt;p&amp;gt;Double encoded &amp;lt;em onclick=alert(1)&amp;gt;"
            "content&amp;lt;/em&amp;gt;&amp;lt;/p&amp;gt;"
            '<<script>alert("bad")//<</script>'
            '<p><a href="ftp://example.test/file" data-extra="x">FTP link</a></p>'
        ),
    )

    assert post["title"] == "<strong>Encoded title</strong>"
    assert "<p>Double encoded <em>content</em></p>" in post["content"]
    assert "<a>FTP link</a>" in post["content"]
    assert_forum_html_is_safe(post["content"])


def test_forum_comment_creation_sanitizes_html(app_module):
    user_id = seed_forum_user(app_module)
    client = TestClient(app_module.app)
    login_forum_user(client)

    post = create_forum_post(client, title="Comment target", content="Post body")
    response = client.post(
        f"/forum/posts/{post['id']}/comment",
        data={
            "content": (
                "<p>Comment <strong onclick=alert(1)>body</strong></p>"
                '<a href="javascript:alert(1)" style="color:red">bad link</a>'
                '<a href="https://example.test/comment">good link</a>'
                "<img src=x onerror=alert(3)>"
            )
        },
    )

    assert response.status_code == 200
    comment = response.json()
    assert comment["user_id"] == user_id
    assert "<p>Comment <strong>body</strong></p>" in comment["content"]
    assert "<a>bad link</a>" in comment["content"]
    assert '<a href="https://example.test/comment">good link</a>' in comment["content"]
    assert_forum_html_is_safe(comment["content"])


def test_forum_post_and_comment_edits_sanitize_html(app_module):
    seed_forum_user(app_module)
    client = TestClient(app_module.app)
    login_forum_user(client)

    post = create_forum_post(client, title="Editable", content="Editable content")
    comment_response = client.post(
        f"/forum/posts/{post['id']}/comment",
        data={"content": "Editable comment"},
    )
    assert comment_response.status_code == 200
    comment = comment_response.json()

    updated_post_response = client.patch(
        f"/forum/post/{post['id']}/update",
        json={
            "title": "<em onclick=alert(1)>Edited title</em><script>bad()</script>",
            "content": (
                '<p>Edited <a href="https://example.test/edited" style="color:red">'
                "safe link</a></p>"
                '<a href="javascript:alert(1)">bad link</a>'
            ),
        },
    )
    updated_comment_response = client.patch(
        f"/forum/comment/{comment['id']}/update",
        data={
            "content": (
                "<p>Edited comment <b onclick=alert(1)>bold</b></p>"
                '<a href="javascript:alert(1)">bad link</a>'
            )
        },
    )

    assert updated_post_response.status_code == 200
    assert updated_comment_response.status_code == 200
    updated_post = updated_post_response.json()
    updated_comment = updated_comment_response.json()

    assert updated_post["title"] == "<em>Edited title</em>bad()"
    assert '<a href="https://example.test/edited">safe link</a>' in updated_post["content"]
    assert "<a>bad link</a>" in updated_post["content"]
    assert "<p>Edited comment <b>bold</b></p>" in updated_comment["content"]
    assert "<a>bad link</a>" in updated_comment["content"]
    assert_forum_html_is_safe(updated_post["title"])
    assert_forum_html_is_safe(updated_post["content"])
    assert_forum_html_is_safe(updated_comment["content"])


def test_forum_reads_resanitize_legacy_dirty_rows_for_list_detail_and_comments(app_module):
    user_id = seed_forum_user(app_module)
    db = app_module.SessionLocal()
    try:
        post = app_module.ForumPost(
            title="<b onclick=alert(1)>Legacy title</b><img src=x>",
            content=(
                "<p>Legacy <strong style='color:red'>formatted</strong> content</p>"
                '<a href="javascript:alert(1)" style="color:red">unsafe link</a>'
            ),
            user_id=user_id,
            upvote_count=0,
            comment_count=1,
        )
        db.add(post)
        db.flush()
        db.add(
            app_module.ForumComment(
                content=(
                    "<em onclick=alert(1)>Legacy comment</em>"
                    '<a href="https://example.test/comment" onclick="bad()">safe link</a>'
                ),
                post_id=post.id,
                user_id=user_id,
            )
        )
        db.commit()
        post_id = post.id
    finally:
        db.close()

    client = TestClient(app_module.app)
    posts_response = client.get("/forum/get_posts")
    post_response = client.get("/forum/get_post", params={"post_id": post_id})
    comments_response = client.get(f"/forum/comments/{post_id}/")

    assert posts_response.status_code == 200
    assert post_response.status_code == 200
    assert comments_response.status_code == 200

    list_post = posts_response.json()[0]
    detail_post = post_response.json()
    comment = comments_response.json()[0]

    for post_payload in [list_post, detail_post]:
        assert post_payload["title"] == "<b>Legacy title</b>"
        assert "<p>Legacy <strong>formatted</strong> content</p>" in post_payload["content"]
        assert "<a>unsafe link</a>" in post_payload["content"]
        assert_forum_html_is_safe(post_payload["title"])
        assert_forum_html_is_safe(post_payload["content"])

    assert "<em>Legacy comment</em>" in comment["content"]
    assert '<a href="https://example.test/comment">safe link</a>' in comment["content"]
    assert_forum_html_is_safe(comment["content"])
