from datetime import datetime, time
from fastapi import APIRouter, HTTPException
from model.parkingCardsModel import ParkingCards
from model.pakingHistoryModel import ParkingHistory
from config.db import conn
from schemas.parkingCardsSchemas import serializeDict, serializeList
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional

parkingCardRoutes = APIRouter()

@parkingCardRoutes.post('/api/card')
def create_new_card(card: ParkingCards):
    try:
        # Kiểm tra các biển số trong danh sách
        for vehicle in card.vehicle:
            # Tìm trong cơ sở dữ liệu xem biển số đã được đăng ký chưa
            if conn.nhaxe.parkingcard.find_one({"vehicle": vehicle}):
                return HTTPException(status_code=404, detail={"msg": f"Biển số này đã được đăng ký."})
        
        card_dict = card.dict()
        card_dict["created_at"] = datetime.utcnow()
        
        create_new_card = conn.nhaxe.parkingcard.insert_one(card_dict)
        
        if create_new_card:
            return {"msg": "success", "data": serializeList(conn.nhaxe.parkingcard.find())}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "msg": "Không thể đăng ký thẻ mới",
            "error": str(e),
        })


@parkingCardRoutes.get("/api/card")
def get_all_parkingcards():
    try:
        card_list = serializeList(conn.nhaxe.parkingcard.find())

        if not card_list:
            return []
        return HTTPException(status_code=200, detail={
            "msg": "success", "data": card_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
@parkingCardRoutes.get("/api/card/{id}")
def get_parkingcard_by_id(id):
    try:
        card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not card:
            return []
        return  HTTPException(status_code=200, detail={
            "msg": "success",
            "data": serializeDict(card)
            })  
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
class updateParkingCardModel(BaseModel):
    vehicle: List[str]
    user: str
    status: str
    role: str
    entrance_time: Optional[datetime]

#Xử lý xe vào    
@parkingCardRoutes.put("/api/card/{id}/input")
def update_in_parkingcard(id: str, card: updateParkingCardModel):
    try:
        existing_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not existing_card:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy thẻ xe này"})

        updated_fields = {
            "vehicle": card.vehicle,
            "user": card.user,
            "status": "Using",
            "role": card.role,
            "entrance_time": card.entrance_time or datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        update_result = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": updated_fields}
        )

    # Record entry in the parking history
        get_data = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        entrance_time = get_data.get("entrance_time")
        history_data = {
            "vehicle": existing_card.get("vehicle"),
            "user": existing_card.get("user"),
            "parkingcard": str(existing_card["_id"]),
            "status": "In",
            "entrance_time": entrance_time,
            "exit_time": "",
            "fee":"",
            "time_at": entrance_time
        }
        
        # Insert the history record
        conn.nhaxe.parkinghistory.insert_one(history_data)

        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail={"msg": "Không có thay đổi nào được thực hiện."})

        updated_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        return {"msg": "success", "data": serializeDict(updated_card)}

    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

# Xử lý xe lấy xe
@parkingCardRoutes.put("/api/card/{id}/output")
def update_out_parkingcard(id: str):
    try:
        # Fetch existing parking card data
        existing_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not existing_card:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy thẻ xe này"})

        # Calculate the fee based on entrance and exit times
        entrance_time = existing_card.get("entrance_time")
        exit_time = datetime.utcnow()
        
        if entrance_time:
            # Calculate the fee
            day_rate = 3000
            night_rate = 10000
            start_day = time(6, 0)   # 6 AM
            end_day = time(18, 0)    # 6 PM
            
            # Determine if the entrance was during the day or night
            if start_day <= entrance_time.time() < end_day:
                fee = day_rate
            else:
                fee = night_rate
        else:
            raise HTTPException(status_code=400, detail={"msg": "Không có thời gian gửi xe để tính phí."})

        # Update the parking card status to 'Not Use'
        updated_fields = {
            "vehicle": [],
            "user": "",
            "status": "Not Use",
            "entrance_time": None,
            "updated_at": exit_time
        }

        # Save to history
        parking_history = {         
            "vehicle": existing_card["vehicle"],
            "user": existing_card["user"],
            "parkingcard": str(existing_card["_id"]),
            "status": "Exited",
            "entrance_time": entrance_time,
            "exit_time": exit_time,
            "fee": fee,
            "time_at": exit_time
        }
        
        #Lưu thông tin thẻ xe ra     
        update_result = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": updated_fields}
        )

        #Lưu vào lịch sử
        conn.nhaxe.parkinghistory.insert_one(parking_history)
       
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail={"msg": "Không có thay đổi nào được thực hiện."})

        updated_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        return {"msg": "success", "data": serializeDict(updated_card)}

    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

class updateRoleCardModel(BaseModel):
    role: str
    
@parkingCardRoutes.put("/api/card/{id}/role")
def update_role_parkingcard(id: str, card: updateRoleCardModel):
    try:
        existing_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        if not existing_card:
            raise HTTPException(status_code=404, detail={"msg": "Không tìm thấy thẻ xe này"})

        updated_fields = {
            "role": card.role,
            "updated_at": datetime.utcnow()  
        }

        update_result = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": updated_fields}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail={"msg": "Không có thay đổi nào được thực hiện."})

        updated_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        return HTTPException(status_code=200, detail={"msg": "success", "data": serializeDict(updated_card)})

    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    
       
@parkingCardRoutes.delete("/api/card/{id}")
def delete_parking_card(id):
    try:
        deleted_card = conn.nhaxe.parkingcard.delete_one({"_id": ObjectId(id)})
        if deleted_card.deleted_count == 0:
            return HTTPException(status_code=404, detail={"msg":"Không tìm thất thẻ xe này"})
        else:
            return HTTPException(status_code=200, detail={"msg":"success", "data": serializeList(conn.nhaxe.parkingcard.find())})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)}) 
       