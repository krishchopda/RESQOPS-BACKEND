from sqlalchemy import Column, Integer, String, Float, Boolean
from core.database import Base

class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="available")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    equipment = Column(String, default="basic")
    is_active = Column(Boolean, default=True)