"""Shared session-backed authentication and directory context helpers."""

from fastapi import Request


def get_current_id(request: Request):
    return request.session.get("user_id", None)


def get_current_role(request: Request):
    return request.session.get("user_role", None)


def get_current_email(request: Request):
    return request.session.get("user_email", None)


def establish_user_session(request: Request, user):
    """Replace the pre-auth session before storing the authenticated identity."""
    request.session.clear()
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role
    request.session["user_id"] = user.id


def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)


def set_teacher_session(request: Request, teacher):
    request.session["state"] = teacher.state
    request.session["county"] = teacher.county
    request.session["district"] = teacher.district
    request.session["school"] = teacher.school
    request.session["teacher"] = teacher.name
