from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional

class Vehicles(BaseModel):
    number_plate: str
    license_name: str = Field(default="")
    vehicle_type: str = Field(default="Car")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None