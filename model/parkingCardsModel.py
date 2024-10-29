from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ParkingCards(BaseModel):
    vehicle: List[str] #Dùng để lưu nhiều biển số xe
    user: str
    status: str = Field(default="Not Use")  #Trạng thái xem thẻ có đang được gửi xe hay không gửi
    role: str = Field(default="default")    #Quyền cho biết thẻ là đăng ký hoặc thẻ thường
    entrance_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None