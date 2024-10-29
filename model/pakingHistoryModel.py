from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParkingHistory(BaseModel):
    vehicle: str
    user: str
    parkingcard: str
    status: str
    entrance_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    fee: str
    time_at: Optional[datetime] = None
    