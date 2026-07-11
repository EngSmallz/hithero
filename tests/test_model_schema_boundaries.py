from backend.db.models import ForumPost, PasswordResetToken, RegisteredUsers, School, TeacherList
from backend.schemas.forum import PostUpdate, VoteInput
from backend.schemas.teachers import TeacherDirectoryResponse, TeacherProfileResponse


def test_orm_models_have_moved_behind_the_db_package_without_table_changes():
    assert School.__module__ == "backend.db.models"
    assert RegisteredUsers.__module__ == "backend.db.models"
    assert TeacherList.__tablename__ == "teacher_list"
    assert ForumPost.__tablename__ == "forum_posts"
    assert PasswordResetToken.__tablename__ == "password_reset_tokens"


def test_request_and_response_dtos_have_moved_behind_schema_packages():
    assert VoteInput.__module__ == "backend.schemas.forum"
    assert PostUpdate.__module__ == "backend.schemas.forum"
    assert TeacherDirectoryResponse.__module__ == "backend.schemas.teachers"
    assert TeacherProfileResponse.__module__ == "backend.schemas.teachers"
