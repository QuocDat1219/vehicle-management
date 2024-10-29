from datetime import datetime
from fastapi import APIRouter, HTTPException
from model.pakingHistoryModel import ParkingHistory
from config.db import conn
from schemas.parkingHistorySchemas import serializeDict, serializeList
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional

ParkingHistoryRoutes = APIRouter()