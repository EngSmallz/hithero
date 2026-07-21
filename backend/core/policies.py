"""Reusable authorization policies for cookie-authenticated mutations."""

from backend.core.errors import DomainError, ForbiddenError


class AuthenticationRequired(DomainError):
    """Raised when a mutation requires a logged-in session."""

    status_code = 401
    default_detail = "You must be logged in."


def require_authenticated_user(user_id, *, detail="You must be logged in."):
    if not user_id:
        raise AuthenticationRequired(detail)
    return user_id


def require_admin(role, *, detail="Access denied: administrator role required."):
    if role != "admin":
        raise ForbiddenError(detail)
    return role


def require_teacher_or_admin(role, *, detail="Access denied."):
    if role not in ("teacher", "admin"):
        raise ForbiddenError(detail)
    return role


def require_owner(current_user_id, owner_id, *, detail="Access denied."):
    if not current_user_id or current_user_id != owner_id:
        raise ForbiddenError(detail)
    return current_user_id


def require_forum_content_owner(
    authorized,
    *,
    detail="Access denied: You must own this forum content.",
):
    if not authorized:
        raise ForbiddenError(detail)
    return True


def require_profile_owner(current_user_id, profile_user_id=None, *, detail="Access denied."):
    profile_user_id = current_user_id if profile_user_id is None else profile_user_id
    return require_owner(current_user_id, profile_user_id, detail=detail)


def require_teacher_district_scope(
    authorized,
    *,
    detail="You can only manage teachers in your own district.",
):
    if not authorized:
        raise ForbiddenError(detail)
    return True
