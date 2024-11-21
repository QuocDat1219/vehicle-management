from datetime import datetime, date
from fastapi import APIRouter, HTTPException
from model.userModel import User
from config.db import conn
from schemas.userSchemas import serializeDict, serializeList, serializeDictDetail
from bson import ObjectId
from pydantic import BaseModel
from typing import List
userRoutes = APIRouter()

@userRoutes.post("/api/user")
def create_new_user(user: User):
    # try:
        # Kiểm tra xem người dùng đã tồn tại chưa
        if conn.nhaxe.user.find_one({"identity_card": user.identity_card}):
            raise HTTPException(status_code=400, detail={"msg": "Người dùng đã đăng ký"})

        # Chuyển đối tượng user thành từ điển và thêm trường created_at
        user_dict = user.dict()

        user_dict["created_at"] = datetime.utcnow()
        created_user = conn.nhaxe.user.insert_one(user_dict)
        
        if created_user:
            return HTTPException(status_code=200, detail={
                "msg": "success",
                "data": serializeList(conn.nhaxe.user.find())
            })
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail={"msg": "Không thể đăng ký người dùng mới", "error": str(e)})


#Lấy danh sách tài khoản
@userRoutes.get("/api/user/")
def get_all_user():
    try:
        # Tìm tất cả người dùng không phải là admin và không lấy trường mật khẩu
        user_list = serializeList(conn.nhaxe.user.find())

        if not user_list:
            return []

        return serializeList(conn.nhaxe.user.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@userRoutes.get("/api/user/{id}")
def get_user_by_id(id):
    try:
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            return []
        return serializeDictDetail(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
# Model for adding new vehicles
class VehicleUpdate(BaseModel):
    vehicle: List[str]

@userRoutes.put("/api/user/{id}/add_vehicle")
def add_vehicle(id: str, vehicle_data: VehicleUpdate):
    try:
        # Tìm id user
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})

        current_vehicles = user.get("vehicle", [])

        # Kiểm tra xem có biển số nào trong danh sách mới đã tồn tại trong danh sách cũ chưa
        existing_vehicles = [v for v in vehicle_data.vehicle if v in current_vehicles]
        if existing_vehicles:
            raise HTTPException(status_code=400, detail={"msg": f"Phương tiện: {', '.join(existing_vehicles)} đã được đăng ký"})

        # Thêm các phương tiện mới vào danh sách của người dùng
        updated_vehicles = current_vehicles + vehicle_data.vehicle
        updated_user = conn.nhaxe.user.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "vehicle": updated_vehicles,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Không cập nhật được phương tiện"})
        
        return serializeList(conn.nhaxe.user.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": f"Phương tiện đã được đăng ký"})

    
@userRoutes.put("/api/user/{id}/remove_vehicle")
def remove_vehicle(id: str, vehicle_data: VehicleUpdate):
    try:
        # Tìm id user
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy khách hàng này"})

        current_vehicles = user.get("vehicle", [])

        # Lọc ra các phương tiện cần xóa
        vehicles_to_remove = vehicle_data.vehicle
        updated_vehicles = [v for v in current_vehicles if v not in vehicles_to_remove]

        # Nếu không có gì để xóa, trả về lỗi
        if len(updated_vehicles) == len(current_vehicles):
            raise HTTPException(status_code=400, detail={"msg": "Không có biển số này"})

        # Cập nhật danh sách phương tiện của người dùng
        updated_user = conn.nhaxe.user.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "vehicle": updated_vehicles,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Cập nhật không thành công"})
        
        return serializeList(conn.nhaxe.user.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

    
# Model cho việc thêm mới biển số xe
class EditVehicleModle(BaseModel):
    full_name: str
    identity_card: str
    address: str
    phone: str
    
# Cập nhật thông tin người dùng
@userRoutes.put("/api/user/{id}")
def add_vehicle(id: str, vehicle_data: EditVehicleModle):
    try:
        # Tìm người dùng theo ID
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            return HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})
        
        # Cập nhật lại người dùng với danh sách biển số mới
        updated_user = conn.nhaxe.user.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "full_name": vehicle_data.full_name,
                "identity_card": vehicle_data.identity_card,
                "address": vehicle_data.address,
                "phone": vehicle_data.phone,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Cập nhật thất bại"})
        
        return serializeList(conn.nhaxe.user.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
@userRoutes.delete("/api/user/{id}")
def delete_user(id):
    try:
        deleted_user = conn.nhaxe.user.delete_one({"_id": ObjectId(id)})
        if deleted_user.deleted_count == 0:
            return HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})
        else:
            return HTTPException(status_code=200, detail={"msg": "success", "data": serializeList(conn.nhaxe.user.find())})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})