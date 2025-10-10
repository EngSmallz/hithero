from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from config import get_db
from services.spotlight_service import SpotlightService
from utils.session import set_session_values

router = APIRouter(prefix="/spotlight", tags=["spotlight"])

@router.get("/{token}")
async def get_spotlight_info(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    spotlight_service = SpotlightService(db)
    spotlight_data = spotlight_service.get_spotlight_info(token)
    
    # Set session values
    session_data = {
        'state': spotlight_data['state'],
        'county': spotlight_data['county']
    }
    
    if spotlight_data['district']:
        session_data['district'] = spotlight_data['district']
    if spotlight_data['school']:
        session_data['school'] = spotlight_data['school']
        session_data['teacher'] = spotlight_data['name']
    
    set_session_values(request, session_data)
    
    return spotlight_data