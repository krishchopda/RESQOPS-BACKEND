from sqlalchemy.orm import Session
from models.hospital import Hospital
from schemas.hospital import HospitalCreate

def get_all_hospitals(db: Session):
    return db.query(Hospital).all()

def create_hospital(db: Session, data: HospitalCreate):
    hospital = Hospital(**data.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital