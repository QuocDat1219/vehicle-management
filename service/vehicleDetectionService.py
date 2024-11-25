import os
import cv2
import sys
import torch
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime, time, timedelta
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from model.parkingCardsModel import ParkingCards
from model.pakingHistoryModel import ParkingHistory
from config.db import conn
from schemas.parkingCardsSchemas import serializeDict
from random import randint
import pytz

sys.path.append(os.path.abspath('yolov5'))
from utils.general import non_max_suppression
from models.experimental import attempt_load

# Tạo router
vehicleDetectionRoutes = APIRouter()

class updateParkingCardModel(BaseModel):
    vehicle: List[str]
    user: str
    status: str
    role: str
    entrance_time: Optional[datetime]

# Lớp phát hiện
class Detection:
    def __init__(self, weights_path='.pt', size=(640, 640), device='cpu', iou_thres=0.5, conf_thres=0.1):
        self.device = device
        self.char_model, self.names = self.load_model(weights_path)
        self.size = size
        self.iou_thres = iou_thres
        self.conf_thres = conf_thres

    def load_model(self, path):
        model = attempt_load(path, map_location=self.device)
        names = model.module.names if hasattr(model, 'module') else model.names
        model.eval()
        return model, names

    def detect(self, frame):
        img, resized_img = self.preprocess_image(frame)
        pred = self.char_model(img)[0]
        detections = non_max_suppression(pred, conf_thres=self.conf_thres, iou_thres=self.iou_thres)
        
        detected_names = []
        for det in detections:
            if len(det):
                for *xyxy, conf, cls in sorted(det, key=lambda x: x[0]):  
                    detected_names.append(self.names[int(cls)])
        
        detected_names_str = "".join(detected_names)
        print(detected_names_str)
        return detected_names_str

    def preprocess_image(self, original_image):
        resized_img = self.resize_img(original_image, size=self.size)
        image = resized_img[:, :, ::-1].transpose(2, 0, 1) 
        image = torch.from_numpy(np.ascontiguousarray(image)).to(self.device).float() / 255.0
        return image.unsqueeze(0), resized_img

    def resize_img(self, img, size):
        h, w = size
        return cv2.resize(img, (w, h))


weights_path = os.path.join(os.path.dirname(__file__), 'char.pt')
detector = Detection(weights_path=weights_path, size=(640, 640), device="cpu", iou_thres=0.5, conf_thres=0.1)
    
@vehicleDetectionRoutes.put("/api/card/entry")
async def upload_license_plate(id_card: str = Form(...), entrance_time: str = Form(...),vehicle_img: str = Form(...), user_img: str = Form(...), file: UploadFile = File(...)):
    try:
        # Đọc ảnh từ file
        # image = np.frombuffer(await file.read(), np.uint8)
        # img = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # # Phát hiện biển số xe
        # detected_plate = detector.detect(img)
        print("xe vàoooooooooooooooooooooooooooooooo")
        #detected_plate = randint(000000, 999999)
        detected_plate = str(945477)
        if not detected_plate:
            return HTTPException(status_code=400, detail="Không phát hiện được phương tiện.")
   
        # Tìm thông tin thẻ (id_card) trong cơ sở dữ liệu
        parking_card = conn.nhaxe.parkingcard.find_one({"id_card": id_card})
        vehicle = None
        # Cập nhật thông tin thẻ tùy thuộc vào role
        if parking_card.get("role") == "Client":
        #Tìm khách hàng
            # Nếu thẻ có role là "client", cập nhật thông tin user (nếu có)
            vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
            if vehicle:
                vehicle_id = vehicle["_id"]
            else:
                return HTTPException(status_code=400, detail="Phương tiện chưa được đăng ký cho thẻ khách hàng!")
        else:

            # Kiểm tra nếu biển số tồn tại trong cơ sở dữ liệu
            vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
            if vehicle:
                vehicle_id = vehicle["_id"]
            else:
                # Nếu không có phương tiện, thêm mới
                vehicle_id = conn.nhaxe.vehicle.insert_one({"number_plate": detected_plate,"vehicle_type": "Motocycle"}).inserted_id

        # Cập nhật danh sách phương tiện vào thẻ
        parking_card["status"] = "Using"
        parking_card["vehicle_img"] =  vehicle_img
        parking_card["user_img"] =  user_img
        parking_card["status"] = "Using"
        parking_card["vehicle"] = list(set(parking_card.get("vehicle", []) + [str(vehicle_id)]))  # Đảm bảo không trùng lặp
        parking_card["entrance_time"] = entrance_time 
        parking_card["updated_at"] = datetime.utcnow()

        # Cập nhật lại thẻ trong cơ sở dữ liệu
        update_result = conn.nhaxe.parkingcard.update_one(
            {"id_card": id_card},
            {"$set": parking_card}
        )

        # Thêm thông tin vào lịch sử
        conn.nhaxe.parkinghistory.insert_one({
            "vehicle": str(vehicle["_id"]),
            "vehicle_img": parking_card["vehicle_img"],
            "user": parking_card.get("user") or "",  # Lấy tên người dùng đầu tiên trong danh sách
            "user_img": parking_card["user_img"],
            "parkingcard": str(parking_card["_id"]),
            "status": "In",
            "entrance_time": parking_card.get("entrance_time"),
            "exit_time": "",
            "fee": "",
            "time_at": datetime.utcnow()
        })

        # Kiểm tra kết quả cập nhật
        if update_result.modified_count == 0:
            return HTTPException(status_code=400, detail="Không nhận diện được thẻ hoặc phương tiện")

        response_result = {
            "vehicle_plate": detected_plate,
            "entrance_time": entrance_time,
            "vehicle_img": parking_card["vehicle_img"]
        }
        return HTTPException(status_code=200, detail={"msg": "Entry Successfully", "data": response_result})

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@vehicleDetectionRoutes.put("/api/card/exit")
async def update_out_parkingcard(
    id_card: str = Form(...),
    exit_time: str = Form(...),
    vehicle_img: str = Form(...),
    user_img: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        print("xe raaaaaaa")
        detected_plate = str(945477)

        if not detected_plate:
            return HTTPException(status_code=400, detail="Không phát hiện được phương tiện.")

        parking_card = conn.nhaxe.parkingcard.find_one({"id_card": id_card})
        if not parking_card:
            return HTTPException(status_code=404, detail="Không tìm thấy thông tin thẻ.")
        vehicle_img_entry = parking_card.get("vehicle_img")
        entrance_time_str = parking_card.get("entrance_time")
        if not entrance_time_str:
            return HTTPException(status_code=400, detail="Không có thời gian gửi xe để tính phí.")

        entrance_time = datetime.strptime(entrance_time_str, "%d/%m/%Y %H:%M:%S")
        exit_time = datetime.strptime(exit_time, "%d/%m/%Y %H:%M:%S")

        vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
        if not vehicle:
            return HTTPException(status_code=404, detail="Phương tiện không tồn tại trong cơ sở dữ liệu.")

        vehicle_type = vehicle.get("vehicle_type")
        if not vehicle_type:
            return HTTPException(status_code=400, detail="Không tìm thấy loại phương tiện.")

        fee_info = conn.nhaxe.fee.find_one({"vehicle_type": vehicle_type})
        if not fee_info:
            return HTTPException(status_code=404, detail="Không tìm thấy thông tin phí.")

        day_time = datetime.strptime(fee_info["day_time"], "%H:%M:%S").time()
        night_time = datetime.strptime(fee_info["night_time"], "%H:%M:%S").time()
        fee_normal = fee_info["fee_normal"]
        fee_night = fee_info["fee_night"]
        fee_day = fee_info["fee_day"]

        # Tính phí
        fee = 0
        entrance_hour = entrance_time.time()
        exit_hour = exit_time.time()

        # Nếu tổng thời gian lớn hơn hoặc bằng 24 giờ, áp dụng phí ngày
        if (exit_time - entrance_time).total_seconds() / 3600 >= 24:
            fee = fee_day
        else:
            if entrance_hour < day_time:  # Xe vào ban đêm
                if exit_hour < day_time:  # Xe ra cũng ban đêm
                    fee = fee_night
                else:  # Xe vào ban đêm nhưng ra ban ngày
                    # time_at_night = (datetime.combine(entrance_time.date(), day_time) - entrance_time).total_seconds() / 3600
                    # time_at_day = (exit_time - datetime.combine(exit_time.date(), day_time)).total_seconds() / 3600
                    fee = fee_night + fee_normal
            elif entrance_hour >= day_time and entrance_hour < night_time:  # Xe vào ban ngày
                if exit_hour < night_time:  # Xe ra cũng ban ngày
                    fee = fee_normal
                else:  # Xe vào ban ngày nhưng ra ban đêm
                    # time_at_day = (datetime.combine(entrance_time.date(), night_time) - entrance_time).total_seconds() / 3600
                    # time_at_night = (exit_time - datetime.combine(exit_time.date(), night_time)).total_seconds() / 3600
                    fee = fee_normal + fee_night
            else:  # Xe vào ban đêm
                if exit_hour < day_time:  # Xe ra cũng ban đêm
                    fee = fee_night
                else:  # Xe vào ban đêm nhưng ra ban ngày
                    # time_at_night = (datetime.combine(entrance_time.date() + timedelta(days=1), day_time) - entrance_time).total_seconds() / 3600
                    # time_at_day = (exit_time - datetime.combine(exit_time.date(), day_time)).total_seconds() / 3600
                    fee = fee_night + fee_normal


        parking_card["status"] = "Not Use"
        parking_card["entrance_time"] = None
        parking_card["updated_at"] = datetime.utcnow()

        conn.nhaxe.parkinghistory.insert_one({
            "vehicle": str(vehicle["_id"]),
            "vehicle_img": vehicle_img,
            "vehicle_img_in": parking_card["vehicle_img"],
            "user": str(parking_card.get("user", "")),
            "user_img": vehicle_img,
            "user_img_in": parking_card["user_img"],
            "parkingcard": str(parking_card["_id"]),
            "status": "Out",
            "entrance_time": entrance_time_str,
            "exit_time": exit_time.strftime("%d/%m/%Y %H:%M:%S"),
            "fee": fee,
            "time_at": datetime.utcnow()
        })
        parking_card["vehicle_img"] = None
        parking_card["user_img"] = None
        update_result = conn.nhaxe.parkingcard.update_one(
            {"id_card": id_card},
            {"$set": parking_card}
        )
        if update_result.modified_count == 0:
            return HTTPException(status_code=400, detail="Không nhận diện được thẻ hoặc phương tiện.")

        response_result = {
            "vehicle_plate_exit": detected_plate,
            "vehicle_plate_entry": vehicle["number_plate"],
            "vehicle_img": vehicle_img_entry,
            "entrance_time": entrance_time_str,
            "exit_time": exit_time.strftime("%d/%m/%Y %H:%M:%S"),
            "fee": fee
        }

        return HTTPException(status_code=200, detail={"msg": "Exited Successfully", "data": response_result})

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


