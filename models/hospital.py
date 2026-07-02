from sqlalchemy import Column, Integer, String, Float
from core.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    total_beds = Column(Integer, default=100)
    available_beds = Column(Integer, default=50)
    trauma_level = Column(Integer, default=3)