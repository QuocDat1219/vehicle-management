import os
import cv2
import sys
import torch
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from model.parkingCardsModel import ParkingCards
from model.pakingHistoryModel import ParkingHistory
from config.db import conn
from schemas.parkingCardsSchemas import serializeDict

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

@vehicleDetectionRoutes.put("/api/card/{id}/detect/in")
async def upload_license_plate(id: str, file: UploadFile = File(...)):
    try:

        image = np.frombuffer(await file.read(), np.uint8)
        img = cv2.imdecode(image, cv2.IMREAD_COLOR)
        print(image)
        return
        # Phát hiện biển số
        detected_plate = detector.detect(img)
        if not detected_plate:
            raise HTTPException(status_code=400, detail="No license plate detected.")

        # Kiểm tra nếu biển số tồn tại hay chưa
        vehicle = conn.nhaxe.vehicle.find_one({"number_plate": detected_plate})
        if vehicle:
            vehicle_id = vehicle["_id"]
        else:
            vehicle_id = conn.nhaxe.vehicle.insert_one({"number_plate": detected_plate}).inserted_id

        # Cập nhật lại thông tin trên thẻ xe
        parking_data = {
            "vehicle": [str(vehicle_id)],
            "user": "Unknown",
            "status": "Using",
            "entrance_time": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        update_result = conn.nhaxe.parkingcard.update_one(
            {"_id": ObjectId(id)},
            {"$set": parking_data}
        )

        # Thêm thông tin vào lịch sử
        existing_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        conn.nhaxe.parkinghistory.insert_one({
            "vehicle": str(vehicle_id),
            "user": existing_card.get("user"),
            "parkingcard": str(existing_card["_id"]),
            "status": "In",
            "entrance_time": existing_card.get("entrance_time"),
            "exit_time": "",
            "fee": "",
            "time_at": datetime.utcnow()
        })

        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the parking card.")

        updated_card = conn.nhaxe.parkingcard.find_one({"_id": ObjectId(id)})
        return {"msg": "success", "data": serializeDict(updated_card)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
