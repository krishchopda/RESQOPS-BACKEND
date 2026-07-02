from sqlalchemy.orm import Session
from models.ambulance import Ambulance
from schemas.ambulance import AmbulanceCreate

def get_all_ambulances(db: Session):
    return db.query(Ambulance).filter(Ambulance.is_active == True).all()

def create_ambulance(db: Session, data: AmbulanceCreate):
    ambulance = Ambulance(**data.model_dump())
    db.add(ambulance)
    db.commit()
    db.refresh(ambulance)
    return ambulance