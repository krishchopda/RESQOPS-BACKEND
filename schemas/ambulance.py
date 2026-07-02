from pydantic import BaseModel

class AmbulanceBase(BaseModel):
    name: str
    status: str = "available"
    latitude: float
    longitude: float
    equipment: str = "basic"

class AmbulanceCreate(AmbulanceBase):
    pass

class AmbulanceResponse(AmbulanceBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}