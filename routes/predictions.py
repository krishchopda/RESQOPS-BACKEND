from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.prediction_service import get_all_predictions

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.get("/")
def predictions(db: Session = Depends(get_db)):
    return get_all_predictions(db)