from datetime import datetime
from fastapi import APIRouter, HTTPException
from model.pakingHistoryModel import ParkingHistory
from config.db import conn
from schemas.parkingHistorySchemas import serializeDict, serializeList, serializeDetail
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional

ParkingHistoryRoutes = APIRouter()

@ParkingHistoryRoutes.get("/api/history")
def get_all_history():
    try:
        all_history = serializeList(conn.nhaxe.parkinghistory.find())
        if not all_history:
            return []
        else:
            return all_history
    except Exception as e:
        return HTTPException(status_code=500, detail={"msg": f"erorr {str(e)}"})
    
@ParkingHistoryRoutes.get("/api/history/{id}/detail")
def get_detail_history(id):
    try:
        history_detail = serializeDetail(conn.nhaxe.parkinghistory.find_one({"_id": ObjectId(id)}))
        if not history_detail:
            return []
        else:
            return history_detail
    except Exception as e:
        return HTTPException(status_code=500, detail={"msg": f"erorr {str(e)}"})    
    