from config.db import conn
from bson import ObjectId

def userEntity(item) -> dict:
    return {
        "id": str(item['_id']),
        "full_name": item['full_name'],
        "identity_card": item['identity_card'],
        "address": item['address'],
        "birth_date": item['birth_date'],
        "vehicle": item['vehicle'],
        "created_at": item.get('created_at', None),
        "updated_at": item.get('updated_at', None),
    }
    
def serializeDict(a) -> dict:
    return {
        **{i:str(a[i]) for i in a if i=='_id'},
        **{i:a[i] for i in a if i!='_id'}
        }

def serializeList(entity) -> list:
    serialized_list = []
    for a in entity:
        vehicle_ids = a.get('vehicle', [])
        vehicles = []

        # Duyệt qua các ObjectId trong danh sách vehicle
        for vehicle_id in vehicle_ids:
            try:
                # Chỉ chuyển đổi vehicle_id thành ObjectId, không phải dict
                vehicle_obj_id = ObjectId(vehicle_id)
            except Exception as e:
                print(f"Invalid ObjectId for vehicle: {vehicle_id}, Error: {e}")  # Debugging
                continue  # Bỏ qua nếu có lỗi khi chuyển đổi

            # Tìm dữ liệu của từng biển số xe từ collection 'vehicle'
            vehicle_data = conn.nhaxe.vehicle.find_one({'_id': vehicle_obj_id})
            if vehicle_data:
                vehicles.append({
                    'number_plate': vehicle_data.get('number_plate', None),
                    '_id': str(vehicle_data['_id'])
                })
            else:
                print(f"No vehicle data found for ID: {vehicle_obj_id}")  # Debugging

        # Xây dựng dictionary cho từng người dùng và thêm danh sách biển số xe
        serialized_dict = {
            "_id": str(a['_id']),
            "full_name": a['full_name'],
            "identity_card": a['identity_card'],
            "address": a['address'],
            "vehicle": vehicles,  # Danh sách biển số xe đã được lấy từ collection 'vehicle'
            "birth_date": a['birth_date'],
            "created_at": a.get('created_at', None),
            "updated_at": a.get('updated_at', None)
        }

        serialized_list.append(serialized_dict)

    return serialized_list


