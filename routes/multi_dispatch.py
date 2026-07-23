from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.multi_dispatch import get_multi_recommendation
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/dispatch", tags=["Dispatch"])

class MultiDispatchRequest(BaseModel):
    incident_id: int
    ambulances_override: Optional[int] = None

@router.post("/recommend-multi")
def recommend_multi(request: MultiDispatchRequest, db: Session = Depends(get_db)):
    return get_multi_recommendation(
        request.incident_id,
        db,
        request.ambulances_override
    )