from sqlalchemy import Column, Integer, String, Float
from core.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, default="active")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)