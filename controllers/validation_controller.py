from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config import get_db
from services.validation_service import ValidationService
from dependencies import get_current_user_id, get_current_user_role

router = APIRouter(prefix="/validation", tags=["validation"])

@router.get("/list/")
async def get_validation_list(
    user_role: str = Depends(get_current_user_role),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    validation_service = ValidationService(db)
    return validation_service.get_validation_list(user_role, user_id)

@router.post("/validate_user/{user_email}")
async def validate_user(
    user_email: str,
    db: Session = Depends(get_db)
):
    validation_service = ValidationService(db)
    return validation_service.validate_user(user_email)

@router.post("/delete_user/{user_email}")
async def delete_user(
    user_email: str,
    user_role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db)
):
    if user_role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="No permission to perform this action"
        )
    
    validation_service = ValidationService(db)
    return validation_service.delete_user(user_email)

@router.post("/report_user/{user_email}")
async def report_user(
    user_email: str,
    db: Session = Depends(get_db)
):
    validation_service = ValidationService(db)
    return validation_service.report_user(user_email)

@router.post("/emailed_user/{user_email}")
async def mark_user_emailed(
    user_email: str,
    db: Session = Depends(get_db)
):
    validation_service = ValidationService(db)
    return validation_service.mark_user_emailed(user_email)