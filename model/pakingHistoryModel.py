from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParkingHistory(BaseModel):
    vehicle: str
    vehicle_img: str
    user: str
    user_img: str
    parkingcard: str
    status: str
    entrance_time: str
    exit_time: str
    fee: str
    time_at: str
    