from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

class User(BaseModel):
    full_name: str
    identity_card: str
    address: str
    birth_date: date
    vehicle: List[str]  #Xe của cá nhân
    created_at: Optional[datetime] = None  # Optional field for created_at
    updated_at: Optional[datetime] = None  # Optional field for created_at
