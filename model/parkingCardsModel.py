from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ParkingCards(BaseModel):
    id_card: str
    vehicle:  Optional[List[str]] = []  #Dùng để lưu nhiều biển số xe
    vehicle_img: Optional[str] = ""
    user: str 
    user_img: Optional[str] = ""
    status: str = Field(default="Not Use")  #Trạng thái xem thẻ có đang được gửi xe hay không gửi
    role: str = Field(default="Normal")    #Quyền cho biết thẻ là đăng ký hoặc thẻ thường
    start_date: str
    end_date: str
    entrance_time: Optional[str] = ""
    card_fee: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None