from types import SimpleNamespace

from backend.services.profile_reads import ProfileReadService


class FakeProfileRepository:
    def __init__(self):
        self.teacher = SimpleNamespace(
            state="IL",
            county="Cook",
            district="District 1",
            school="Example School",
            name="Example Teacher",
            wishlist_url="https://example.test/wishlist",
            about_me="Books",
            image_data=b"image-bytes",
            regUserID=42,
            url_id="example-teacher",
        )

    def get_teacher_by_context(self, context):
        self.context = context
        return self.teacher

    def get_teacher_by_user_id(self, user_id):
        self.user_id = user_id
        return self.teacher


def test_profile_read_service_serializes_teacher_info_and_image():
    repository = FakeProfileRepository()
    service = ProfileReadService(repository)

    result = service.get_teacher_info({"state": "IL"})

    assert result["name"] == "Example Teacher"
    assert result["image_data"] == "aW1hZ2UtYnl0ZXM="
    assert "regUserID" not in result


def test_profile_read_service_returns_session_context_and_access_policy():
    repository = FakeProfileRepository()
    service = ProfileReadService(repository)

    teacher, session_data = service.get_myinfo(42)

    assert teacher.name == "Example Teacher"
    assert session_data["teacher"] == "Example Teacher"
    assert service.has_teacher_access({}, 42, "teacher") is True
    assert service.has_teacher_access({}, 7, "teacher") is False
    assert service.has_teacher_access({}, 42, "admin") is False
    assert service.get_teacher_url({}) == "/teacher/example-teacher"


def test_profile_read_service_serializes_current_teacher_without_account_fields():
    service = ProfileReadService(FakeProfileRepository())

    result = service.get_current_teacher(42)

    assert result == {
        "name": "Example Teacher",
        "url_id": "example-teacher",
        "state": "IL",
        "county": "Cook",
        "district": "District 1",
        "school": "Example School",
        "wishlist_url": "https://example.test/wishlist",
        "about_me": "Books",
        "image_data": "aW1hZ2UtYnl0ZXM=",
    }
    assert "regUserID" not in result
