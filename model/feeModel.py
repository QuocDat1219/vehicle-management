from pydantic import BaseModel, Field
from datetime import time
from typing import Optional

class FeeVehicle(BaseModel):
    vehicle_type: str
    day_time: time  # Thời gian ban ngày (hh:mm:ss)
    night_time: time  # Thời gian ban đêm (hh:mm:ss)
    fee_normal: int  # Phí thông thường
    fee_night: int  # Phí ban đêm
    fee_day: int  # Phí cả ngày
    fee_surcharge: int  # Phụ phí
