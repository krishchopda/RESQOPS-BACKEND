
from pydantic import BaseModel

class HospitalBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    total_beds: int = 100
    available_beds: int = 50
    trauma_level: int = 3

class HospitalCreate(HospitalBase):
    pass

class HospitalResponse(HospitalBase):
    id: int

    model_config = {"from_attributes": True}