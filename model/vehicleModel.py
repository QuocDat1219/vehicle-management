from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Vehicles(BaseModel):
    number_plate: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None