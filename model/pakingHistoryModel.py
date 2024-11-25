from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParkingHistory(BaseModel):
    vehicle: str
    vehicle_img: str
    vehicle_img_in: str
    user: str
    user_img: str
    user_img_in: str
    parkingcard: str
    status: str
    entrance_time: str
    exit_time: str
    fee: int
    time_at: str
    
    