from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

class User(BaseModel):
    moto_fee_day: int
    moto_fee_night: int
    car_fee_day: int
    car_fee_night: int
    vehicle: List[str]  #Xe của cá nhân
    created_at: Optional[datetime] = None  # Optional field for created_at
    updated_at: Optional[datetime] = None  # Optional field for created_at
