from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Customer(BaseModel):
    fullname: str
    address: str
    phone: str
    username: str
    password: str  
    role: str = Field(default="user")
    created_at: Optional[datetime] = None
