"""Shared session-backed authentication and directory context helpers."""

from fastapi import Request


def get_current_id(request: Request):
    return request.session.get("user_id", None)


def get_current_role(request: Request):
    return request.session.get("user_role", None)


def get_current_email(request: Request):
    return request.session.get("user_email", None)


def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)


def set_teacher_session(request: Request, teacher):
    request.session["state"] = teacher.state
    request.session["county"] = teacher.county
    request.session["district"] = teacher.district
    request.session["school"] = teacher.school
    request.session["teacher"] = teacher.name
