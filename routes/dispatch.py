from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.dispatch_engine import get_recommendation

router = APIRouter(prefix="/dispatch", tags=["Dispatch"])

@router.get("/recommend/{incident_id}")
def recommend(incident_id: int, db: Session = Depends(get_db)):
    return get_recommendation(incident_id, db)