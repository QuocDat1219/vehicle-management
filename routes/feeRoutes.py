from datetime import time
from fastapi import APIRouter, HTTPException
from model.feeModel import FeeVehicle
from config.db import conn
from schemas.feeSchemas import serializeDict, serializeList
from bson import ObjectId
from pydantic import BaseModel

feeRoutes = APIRouter()

@feeRoutes.post("/api/fee")
def create_fee(fee: FeeVehicle):
    try:
        if conn.nhaxe.fee.find_one({"vehicle_type": fee.vehicle_type}):
            return HTTPException(status_code=400, detail={"msg": "Phí của loại phương tiện này đã được tạo!"})
        # Chuyển đổi các trường `datetime.time` sang chuỗi
        fee_data = fee.dict()
        fee_data["day_time"] = fee.day_time.strftime("%H:%M:%S")
        fee_data["night_time"] = fee.night_time.strftime("%H:%M:%S")
        
        # Lưu vào MongoDB
        created_fee = conn.nhaxe.fee.insert_one(fee_data)
        if created_fee:
            return HTTPException(status_code=200, detail={
                "msg": "success",
                "data": serializeList(conn.nhaxe.fee.find())
            })
    except Exception as e:
        return HTTPException(status_code=500, detail={"msg":f"error: {str(e)}"})
    
@feeRoutes.get("/api/fee")
def get_all_fee():
    try:
        all_fee = serializeList(conn.nhaxe.fee.find())
        if not all_fee:
            return []
        else:
            return all_fee
    except Exception as e:
        return HTTPException(status_code=200, detail={
        "msg": f"error: {str(e)}",
        })

@feeRoutes.get("/api/fee/{id}")
def get_fee(id: str):
    try:
        fee = serializeDict(conn.nhaxe.fee.find_one({"_id": ObjectId(id)}))
        if not fee:
            return []
        else:
            return fee
    except Exception as e:
        return HTTPException(status_code=500, detail={
        "msg": f"error: {str(e)}",
        })

class FeeEditModel(BaseModel):
    day_time: time
    night_time: time
    fee_normal: int
    fee_night: int
    fee_day: int
    fee_surcharge: int
    
@feeRoutes.put("/api/fee/{id}")
def edit_fee(id: str, edit_data: FeeEditModel):
    try:
        updated_fee = conn.nhaxe.fee.update_one(
            {"_id": ObjectId(id)},
            {"$set": { 
                "day_time": edit_data.day_time.strftime("%H:%M:%S"),
                "night_time": edit_data.night_time.strftime("%H:%M:%S"),
                "fee_normal": edit_data.fee_normal,
                "fee_night": edit_data.fee_night,
                "fee_day": edit_data.fee_day,
                "fee_surcharge": edit_data.fee_surcharge,
                }})
        if updated_fee.modified_count == 0:
            return HTTPException(status_code=404, detail={"msg": "Cập nhật thất bại"})
        return HTTPException(status_code=200, detail={
            "msg":"success",
            "data": serializeList(conn.nhaxe.fee.find())})
    except Exception as e:
        return HTTPException(status_code=200, detail={
        "msg": f"error: {str(e)}",
        })

@feeRoutes.delete("/api/fee/{id}")
def delete_fee(id: str):
    try:
        deleted_fee = conn.nhaxe.fee.delete_one({"_id": ObjectId(id)})
        if deleted_fee.deleted_count == 0:
            return HTTPException(status_code=404, detail={"msg": "Không thể xóa phí này!"})
        else:
            return HTTPException(status_code=200, detail={"msg": "success", "data": serializeList(conn.nhaxe.fee.find())})       
    except Exception as e:
        return HTTPException(status_code=200, detail={
        "msg": f"error: {str(e)}",
        })       