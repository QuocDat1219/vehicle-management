from datetime import datetime, date
from fastapi import APIRouter, HTTPException
from model.userModel import User
from config.db import conn
from schemas.userSchemas import serializeDict, serializeList
from bson import ObjectId
from pydantic import BaseModel
userRoutes = APIRouter()

@userRoutes.post("/api/user")
def create_new_user(user: User):
    try:
        # Kiểm tra xem người dùng đã tồn tại chưa
        if conn.nhaxe.user.find_one({"identity_card": user.identity_card}):
            raise HTTPException(status_code=400, detail={"msg": "Người dùng đã đăng ký"})

        # Chuyển đối tượng user thành từ điển và thêm trường created_at
        user_dict = user.dict()

        # Chuyển đổi birth_date (nếu có) từ date thành datetime
        if "birth_date" in user_dict:
            user_dict["birth_date"] = datetime.combine(user_dict["birth_date"], datetime.min.time())

        user_dict["created_at"] = datetime.utcnow()
        created_user = conn.nhaxe.user.insert_one(user_dict)
        
        if created_user:
            return HTTPException(status_code=200, detail={
                "msg": "success",
                "data": serializeList(conn.nhaxe.user.find())
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Không thể đăng ký người dùng mới", "error": str(e)})


#Lấy danh sách tài khoản
@userRoutes.get("/api/user/")
def get_all_user():
    try:
        # Tìm tất cả người dùng không phải là admin và không lấy trường mật khẩu
        user_list = serializeList(conn.nhaxe.user.find())

        if not user_list:
            return []

        return HTTPException(status_code=200, detail={
            "msg": "success",
            "data": user_list
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@userRoutes.get("/api/user/{id}")
def get_user_by_id(id):
    try:
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            return []
        return  HTTPException(status_code=200, detail={
            "msg": "success",
            "data": serializeDict(user)
            })  
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
# Model cho việc thêm mới biển số xe
class VehicleUpdate(BaseModel):
    vehicle: str

# Cập nhật thông tin người dùng và thêm biển số mới
@userRoutes.put("/api/user/{id}/add_vehicle")
def add_vehicle(id: str, vehicle_data: VehicleUpdate):
    try:
        # Tìm người dùng theo ID
        user = conn.nhaxe.user.find_one({"_id": ObjectId(id)})
        if not user:
            return HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})

        # Lấy danh sách biển số xe hiện tại
        current_vehicles = user.get("vehicle", [])

        # Kiểm tra xem biển số đã tồn tại chưa
        if vehicle_data.vehicle in current_vehicles:
            raise HTTPException(status_code=400, detail={"msg": "Biển số này đã tồn tại"})

        # Thêm biển số mới vào danh sách
        current_vehicles.append(vehicle_data.vehicle)

        # Cập nhật lại người dùng với danh sách biển số mới
        updated_user = conn.nhaxe.user.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "vehicle": current_vehicles,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Cập nhật thất bại"})
        
        return {"msg": "success", "data": serializeDict(conn.nhaxe.user.find())}
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