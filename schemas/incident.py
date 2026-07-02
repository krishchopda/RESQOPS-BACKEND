from pydantic import BaseModel
from typing import Optional

class IncidentBase(BaseModel):
    type: str
    severity: str
    latitude: float
    longitude: float
    description: Optional[str] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    status: str

    model_config = {"from_attributes": True}