from types import SimpleNamespace

from backend.services.teacher_directory import TeacherDirectoryService


class FakeTeacherRepository:
    def count_public_teachers(self, **filters):
        self.count_filters = filters
        return 3

    def list_public_teachers(self, **kwargs):
        self.list_kwargs = kwargs
        return [
            SimpleNamespace(
                name="Example Teacher",
                url_id="example-teacher",
                state="IL",
                county="Cook",
                district="District 1",
                school="Example School",
            )
        ]

    def directory_filters(self, **filters):
        self.directory_filter_args = filters
        return {"states": ["IL"], "counties": ["Cook"], "districts": [], "schools": []}

    def get_public_teacher(self, url_id):
        self.profile_url_id = url_id
        return SimpleNamespace(
            name="Example Teacher",
            url_id=url_id,
            state="IL",
            county="Cook",
            district="District 1",
            school="Example School",
            wishlist_url="https://example.test/wishlist",
            about_me="Books",
            image_data=None,
            private_email="private@example.test",
        )


def test_directory_service_normalizes_filters_and_pagination():
    repository = FakeTeacherRepository()
    service = TeacherDirectoryService(repository)

    response = service.build_directory_response(
        state=" IL ", county=" ", page=9, page_size=200
    )

    assert response["page"] == 1
    assert response["page_size"] == 100
    assert response["applied_filters"] == {
        "state": "IL",
        "county": None,
        "district": None,
        "school": None,
    }
    assert repository.list_kwargs["offset"] == 0
    assert repository.list_kwargs["limit"] == 100


def test_directory_service_profile_serialization_excludes_private_fields():
    repository = FakeTeacherRepository()
    service = TeacherDirectoryService(repository)

    profile = service.get_public_teacher_profile("example-teacher")

    assert profile["name"] == "Example Teacher"
    assert "private_email" not in profile
