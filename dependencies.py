from fastapi import Request, HTTPException

def get_current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id

def get_current_user_role(request: Request) -> str:
    role = request.session.get("user_role")
    if not role:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return role

def get_current_user_email(request: Request) -> str:
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return email

def get_optional_user_id(request: Request) -> int | None:
    return request.session.get("user_id")

def get_optional_user_role(request: Request) -> str | None:
    return request.session.get("user_role")