import os
import cv2
import sys
import torch
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime, time
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


@vehicleDetectionRoutes.put("/api/card/detect")
async def manage_parkingcard(id_card: str = Form(...), entrance_time: str = Form(...), file: UploadFile = File(...)):
    try:
        existing_card = conn.nhaxe.parkingcard.find_one({"id_card": id_card})
        if not existing_card:
            return HTTPException(status_code=404, detail={"msg": "Thẻ chưa được đăng ký"})
        # Kiểm tra trạng thái thẻ
        if existing_card["status"] == "Using":
            # Nếu thẻ đang sử dụng, gọi hàm xe ra
            return await update_out_parkingcard(id_card=id_card, entrance_time=entrance_time, file=file)
        elif existing_card["status"] == "Not Use":
            # Nếu thẻ chưa sử dụng, gọi hàm xe vào
            return await upload_license_plate(id_card=id_card, entrance_time=entrance_time, file=file)
        else:
            return HTTPException(status_code=400, detail={"msg": "Trạng thái thẻ không hợp lệ."})

    except Exception as e:
        return HTTPException(status_code=500, detail={"msg": str(e), "data":"aaaaaaa"})
    
@vehicleDetectionRoutes.put("/api/card/entry")
async def upload_license_plate(id_card: str = Form(...), entrance_time: str = Form(...), file: UploadFile = File(...)):
    try:
        # Đọc ảnh từ file
        # image = np.frombuffer(await file.read(), np.uint8)
        # img = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # # Phát hiện biển số xe
        # detected_plate = detector.detect(img)
        print("xe vàoooooooooooooooooooooooooooooooo")
        print(entrance_time)
        #detected_plate = randint(000000, 999999)
        detected_plate = str(945477)
        if not detected_plate:
            return HTTPException(status_code=400, detail="Không phát hiện được phương tiện.")
   
        # Tìm thông tin thẻ (id_card) trong cơ sở dữ liệu
        parking_card = conn.nhaxe.parkingcard.find_one({"id_card": id_card})
        user_card = None
        # Cập nhật thông tin thẻ tùy thuộc vào role
        if parking_card.get("role") == "Client":
        #Tìm khách hàng
         
            user_card = conn.nhaxe.user.find_one({"_id": ObjectId(parking_card["user"])})
            # Nếu thẻ có role là "client", cập nhật thông tin user (nếu có)
            vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
            if vehicle:
                vehicle_id = vehicle["_id"]
            else:
                return HTTPException(status_code=400, detail="Phương tiện chưa được đăng ký cho thẻ khách hàng!")
        else:
            # Nếu thẻ có role là "normal", gán user là "Rỗng"
            # Kiểm tra nếu biển số tồn tại trong cơ sở dữ liệu
            vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
            if vehicle:
                vehicle_id = vehicle["_id"]
            else:
                # Nếu không có phương tiện, thêm mới
                vehicle_id = conn.nhaxe.vehicle.insert_one({"number_plate": detected_plate}).inserted_id

        # Cập nhật danh sách phương tiện vào thẻ
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
            "vehicle": str(vehicle_id),
            "user": parking_card.get("user", ["Rỗng"])[0],  # Lấy tên người dùng đầu tiên trong danh sách
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
            "user_card": user_card.get("full_name") if user_card else None,
            "vehicle_plate": detected_plate,
            "entrance_time": entrance_time
        }
        return HTTPException(status_code=200, detail={"msg": "Entry Successfully", "data": response_result})

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@vehicleDetectionRoutes.put("/api/card/exit")
async def update_out_parkingcard(id_card: str = Form(...), entrance_time: str = Form(...), file: UploadFile = File(...)):
    try:
        # Phát hiện biển số xe (giả lập)
        print("xe raaaaaaa")
        detected_plate = str(945477)

        if not detected_plate:
            return HTTPException(status_code=400, detail="Không phát hiện được phương tiện.")

        # Tìm thông tin thẻ (id_card) trong cơ sở dữ liệu
        parking_card = conn.nhaxe.parkingcard.find_one({"id_card": id_card})
        if not parking_card:
            return HTTPException(status_code=404, detail="Không tìm thấy thông tin thẻ.")

        # Chuyển entrance_time (chuỗi ISO) thành đối tượng datetime
        entrance_time_fee = parking_card.get("entrance_time")
        if entrance_time_fee:
            # Chuyển entrance_time từ chuỗi ISO thành datetime
            entrance_time_fee = datetime.fromisoformat(entrance_time_fee.replace("Z", "+00:00"))
            print(entrance_time_fee)
            # Tính phí
            day_rate = 3000
            night_rate = 10000
            start_day = time(6, 0)  # 6 AM
            end_day = time(18, 0)   # 6 PM

            if start_day <= entrance_time_fee.time() < end_day:
                fee = day_rate
            else:
                fee = night_rate
        else:
            return HTTPException(status_code=400, detail="Không có thời gian gửi xe để tính phí.")

        # Kiểm tra phương tiện đã được phát hiện
        vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
        if not vehicle:
            return HTTPException(status_code=404, detail="Phương tiện không tồn tại trong cơ sở dữ liệu.")

        user_card = None  # Khởi tạo mặc định
        registered_vehicles = parking_card.get("vehicle", [])  # Khởi tạo danh sách phương tiện mặc định

        # Kiểm tra role và phương tiện
        if parking_card.get("role") == "Client":
            # Tìm khách hàng
            user_card = conn.nhaxe.user.find_one({"_id": ObjectId(parking_card["user"])})
            # Kiểm tra phương tiện phát hiện có trong danh sách phương tiện đã đăng ký
            if str(vehicle["_id"]) not in registered_vehicles:
                return HTTPException(status_code=400, detail="Phương tiện không trùng với phương tiện đã đăng ký trên thẻ!")
            fee = fee / 2  # Giảm phí cho 'Client'

        elif parking_card.get("role") == "Normal":
            # Nếu thẻ là "Normal", chỉ cho phép phương tiện trùng với phương tiện đầu tiên
            if registered_vehicles and str(vehicle["_id"]) != registered_vehicles[0]:
                return HTTPException(status_code=400, detail="Phương tiện không trùng với phương tiện đã đăng ký trên thẻ!")
            # Xóa phương tiện nếu thẻ là "Normal"
            if registered_vehicles:
                conn.nhaxe.vehicle.delete_one({"_id": ObjectId(registered_vehicles[0])})
            parking_card["vehicle"] = []  # Xóa danh sách phương tiện

        # Cập nhật trạng thái thẻ
        parking_card["status"] = "Not Use"  # Đổi trạng thái thẻ
        parking_card["entrance_time"] = None
        parking_card["updated_at"] = datetime.utcnow()

        # Thêm thông tin vào lịch sử
        conn.nhaxe.parkinghistory.insert_one({
            "vehicle": str(vehicle["_id"]),
            "user": parking_card.get("user", "Rỗng"),
            "parkingcard": str(parking_card["_id"]),
            "status": "Out",
            "entrance_time": entrance_time_fee,
            "exit_time": entrance_time,
            "fee": fee,
            "time_at": entrance_time
        })

        # Cập nhật lại thẻ trong cơ sở dữ liệu
        update_result = conn.nhaxe.parkingcard.update_one(
            {"id_card": id_card},
            {"$set": parking_card}
        )
        if update_result.modified_count == 0:
            return HTTPException(status_code=400, detail="Không nhận diện được thẻ hoặc phương tiện.")

        # Kết quả trả về
        response_result = {
            "user_card": user_card.get("full_name") if user_card else None,
            "vehicle_plate": detected_plate,
            "entrance_time": entrance_time_fee.isoformat(),
            "exit_time": entrance_time,
            "fee": fee
        }
        return HTTPException(status_code=200, detail={"msg": "Exited Successfully", "data": response_result})

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

