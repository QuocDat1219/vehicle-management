from datetime import datetime, time
from fastapi import APIRouter, HTTPException
from model.parkingCardsModel import ParkingCards
from model.pakingHistoryModel import ParkingHistory
from model.vehicleModel import Vehicles
from config.db import conn
from schemas.parkingCardsSchemas import serializeDict, serializeList, serializeDictDetail
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional

parkingCardRoutes = APIRouter()

@parkingCardRoutes.post('/api/card')
def create_new_card(card: ParkingCards):
    # try:
        # Check if id_card already exists
        if conn.nhaxe.parkingcard.find_one({"id_card": card.id_card}):
            return HTTPException(status_code=400, detail={"msg": "Thẻ đã được đăng ký"})
        
        # Set default values if not provided
        card_dict = card.dict()
        card_dict["vehicle"] = card_dict.get("vehicle", [])
        card_dict["vehicle_img"] = card_dict.get("vehicle_img","")
        card_dict["user"] = card_dict.get("user", "")
        card_dict["user_img"] = card_dict.get("user_img","")
        card_dict["status"] = card_dict.get("status", "Not Use")
        card_dict["role"] = card_dict.get("role", "default")
        card_dict["start_date"] = card_dict.get("start_date", "")
        card_dict["end_date"] = card_dict.get("end_date", "")
        card_dict["entrance_time"] = card_dict.get("entrance_time", "")
        card_dict["card_fee"] = card_dict.get("card_fee", 0)
        card_dict["created_at"] = datetime.utcnow()

        # Insert new card
        create_new_card = conn.nhaxe.parkingcard.insert_one(card_dict)
        
        if create_new_card:
            return serializeList(conn.nhaxe.parkingcard.find())
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail={
    #         "msg": "Không thể đăng ký thẻ mới",
    #         "error": str(e),
    #     })


@parkingCardRoutes.get("/api/card")
def get_all_parkingcards():
    try:
        card_list = serializeList(conn.nhaxe.parkingcard.find())

        if not card_list:
            return []
        return card_list
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
@parkingCardRoutes.get("/api/card/{id}")
def get_parkingcard_by_id(id):
    try:
        card = conn.nhaxe.parkingcard.find_one({"id_card": id})
        if not card:
            return []
        return  card
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
@parkingCardRoutes.get("/api/card/{id}/detail")
def get_parkingcard_by_id(id):
    try:
        card = serializeDictDetail(conn.nhaxe.parkingcard.find_one({"id_card": id}))
        if not card:
            return []
        return  card
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

# Model for adding new vehicles
class VehicleUpdate(BaseModel):
    vehicle: List[str]

@parkingCardRoutes.put("/api/card/{id}/add_vehicle")
def add_vehicle(id: str, vehicle_data: VehicleUpdate):
    try:
        # Tìm id user
        user = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not user:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy người dùng này"})

        current_vehicles = user.get("vehicle", [])

        # Kiểm tra xem có biển số nào trong danh sách mới đã tồn tại trong danh sách cũ chưa
        existing_vehicles = [v for v in vehicle_data.vehicle if v in current_vehicles]
        if existing_vehicles:
            raise HTTPException(status_code=400, detail={"msg": f"Phương tiện: {', '.join(existing_vehicles)} đã được đăng ký"})

        # Thêm các phương tiện mới vào danh sách của người dùng
        updated_vehicles = current_vehicles + vehicle_data.vehicle
        updated_user = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "vehicle": updated_vehicles,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Không cập nhật được phương tiện"})
        
        return serializeList(conn.nhaxe.parkingcard.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": f"Phương tiện đã được đăng ký"})

    
@parkingCardRoutes.put("/api/card/{id}/remove_vehicle")
def remove_vehicle(id: str, vehicle_data: VehicleUpdate):
    try:
        # Tìm id user
        user = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
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
        updated_user = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "vehicle": updated_vehicles,
                "updated_at": datetime.utcnow()
            }}
        )

        if updated_user.modified_count == 0:
            raise HTTPException(status_code=404, detail={"msg": "Cập nhật không thành công"})
        
        return serializeList(conn.nhaxe.parkingcard.find())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

class updateRoleCardModel(BaseModel):
    role: str
    user: str
    start_date: str
    end_date: str
    
@parkingCardRoutes.put("/api/card/{id}/role")
def update_role_parkingcard(id: str, card: updateRoleCardModel):
    try:
        existing_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not existing_card:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy thẻ xe này"})

        updated_fields = {
            "role": card.role,
            "user": card.user,
            "start_date": card.start_date,
            "end_date": card.end_date,
            "updated_at": datetime.utcnow()  
        }

        update_result = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": updated_fields}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail={"msg": "Không có thay đổi nào được thực hiện."})

        updated_card = serializeList(conn.nhaxe.parkingcard.find())
        return HTTPException(status_code=200, detail={"msg": "success", "data": updated_card})

    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
       
@parkingCardRoutes.delete("/api/card/{id}")
def delete_parking_card(id):
    try:
        deleted_card = conn.nhaxe.parkingcard.delete_one({"id_card": id})
        if deleted_card.deleted_count == 0:
            return HTTPException(status_code=404, detail={"msg":"Không tìm thất thẻ xe này"})
        else:
            return HTTPException(status_code=200, detail={"msg":"success", "data": serializeList(conn.nhaxe.parkingcard.find())})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)}) 
       