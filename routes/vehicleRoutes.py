from datetime import datetime, date
from fastapi import APIRouter, HTTPException
from model.vehicleModel import Vehicles
from config.db import conn
from schemas.vehicleSchemas import serializeDict, serializeList
from bson import ObjectId
from pydantic import BaseModel

vehicleRoutes = APIRouter()

@vehicleRoutes.post("/api/vehicle")
def register_vehicle(vehicle: Vehicles):
    try:
        if conn.nhaxe.vehicle.find_one({"number_plate": vehicle.number_plate}):
            return HTTPException(status_code=400, detail={
                "msg": "Biển số xe đã được đăng ký"
            })
        
        vehicle_dict = vehicle.dict()
        vehicle_dict["created_at"] = datetime.utcnow()
        created_vehicle = conn.nhaxe.vehicle.insert_one(vehicle_dict)
        
        if created_vehicle:
            return HTTPException(status_code=200, detail={
                "msg": "success",
                "data": serializeList(conn.nhaxe.vehicle.find())
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "msg": "Không thể đăng ký biển số xe mới",
            "error": str(e)
        })


@vehicleRoutes.get('/api/vehicle')
def get_all_vehicle():
    try:
        vehicle_list = serializeList(conn.nhaxe.vehicle.find())
        
        if not vehicle_list:
            return []
        
        return serializeList(conn.nhaxe.vehicle.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "msg": str(e)
        })
        
@vehicleRoutes.get('/api/vehicle/{id}')
def get_vehicle_by_id(id):
    try:
        vehicle = serializeDict(conn.nhaxe.vehicle.find_one(
            {"_id": ObjectId(id)}))
        
        if not vehicle:
            return []
        return serializeDict(vehicle)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

class updateVehicleModel(BaseModel):
    number_plate: str
    license_name: str
    vehicle_type: str
    
@vehicleRoutes.put('/api/vehicle/{id}')
def update_vehicle(id: str, vehicle_data: updateVehicleModel):
    try:
        vehicle = serializeDict(conn.nhaxe.vehicle.find_one(
            {"_id": ObjectId(id)}))
        
        if not vehicle:
            raise HTTPException(status_code=404, detail={
                "msg": "Không tìm thấy phương tiện này"
            })
            
        updated_vehicle = conn.nhaxe.vehicle.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "number_plate": vehicle_data.number_plate,
                "license_name": vehicle_data.license_name,
                "vehicle_type": vehicle_data.vehicle_type,
                "updated_at": datetime.utcnow()
            }})
        
        if updated_vehicle.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Cập nhật thất bại"})
        
        return {"msg": "success", "data": serializeList(conn.nhaxe.vehicle.find())}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    

@vehicleRoutes.delete("/api/vehicle/{id}")
def delete_vehicle(id):
    try:
        delete_vehicle = conn.nhaxe.vehicle.delete_one({"_id": ObjectId(id)})
        if delete_vehicle.deleted_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})
        else:
            return HTTPException(status_code=200, detail={"msg": "success", "data": serializeList(conn.nhaxe.vehicle.find())})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})