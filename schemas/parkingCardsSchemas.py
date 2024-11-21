from config.db import conn
from bson import ObjectId
import pytz

def parkingcardEntity(item) -> dict:
    return {
        "id": str(item['_id']),
        "id_card": item['id_card'],
        "vehicle": item['vehicle'],
        "vehicle_img": item['vehicle_img'],
        "user": item['user'],
        "user_img": item['user_img'],
        "status": item['status'],
        "role": item['role'],
        "start_date": item['start_date'],
        "end_date": item['end_date'],
        "entrance_time": item['entrance_time'],
        "card_fee": item['card_fee'],
        "created_at": item.get['created_at', None],
        "updated_at": item.get['updated_at', None]
    }

def serializeDict(a) -> dict:
    return {**{i:str(a[i]) for i in a if i=='_id'},**{i:a[i] for i in a if i!='_id'}}

def serializeDictDetail(a) -> dict:
    # Lấy thông tin phương tiện dựa trên danh sách ID xe trong thẻ đỗ xe
    vehicle_ids = a.get('vehicle', [])
    vehicles = []
    for vehicle_id in vehicle_ids:
        try:
            vehicle_obj_id = ObjectId(vehicle_id)
        except Exception:
            continue

        # Lấy dữ liệu xe từ bảng vehicle
        vehicle_data = conn.nhaxe.vehicle.find_one({'_id': vehicle_obj_id})
        if vehicle_data:
            vehicles.append({
                'number_plate': vehicle_data.get('number_plate', None),
                'license_name': vehicle_data.get('license_name', None),
                'vehicle_type': vehicle_data.get('vehicle_type', None),
                '_id': str(vehicle_data['_id'])
            })

    # Lấy thông tin người dùng dựa trên ID người dùng trong thẻ đỗ xe
    user_id = a.get('user')
    user_data = None
    if user_id:
        try:
            user_obj_id = ObjectId(user_id)
        except Exception:
            user_data = None
        else:
            # Lấy dữ liệu người dùng từ bảng user
            user_info = conn.nhaxe.user.find_one({'_id': user_obj_id})
            if user_info:
                user_data = {
                    'full_name': user_info.get('full_name', None),
                    '_id': str(user_info['_id'])
                }

    # Trả về thông tin chi tiết của thẻ đỗ xe
    return {
        "_id": str(a['_id']),
        "id_card": a.get('id_card'),
        "vehicle": vehicles,  # List of vehicles with details
        "vehicle_img": a.get('vehicle_img',""),
        "user_card": user_data,  # User details (name and _id)
        "user_img": a.get('user_img',""),   
        "status": a.get('status'),
        "role": a.get('role'),
        "start_date": a.get('start_date', None),
        "end_date": a.get('end_date', None),
        "entrance_time": a.get('entrance_time'),
        "card_fee": a.get('card_fee', 0),
        "created_at": a.get('created_at', None),
        "updated_at": a.get('updated_at', None)
    }
    
def serializeList(entity) -> list:
    serialized_list = []
    for a in entity:
        # Retrieve vehicle data based on the vehicle IDs stored in the parking card
        vehicle_ids = a.get('vehicle', [])
        vehicles = []
        for vehicle_id in vehicle_ids:
            try:
                # Ensure vehicle_id is a valid ObjectId
                vehicle_obj_id = ObjectId(vehicle_id)
            except Exception as e:
                print(f"Invalid ObjectId for vehicle: {vehicle_id}, Error: {e}")
                continue

            # Fetch the vehicle data from the vehicle collection
            vehicle_data = conn.nhaxe.vehicle.find_one({'_id': vehicle_obj_id})
            if vehicle_data:
                vehicles.append({
                    'number_plate': vehicle_data.get('number_plate', None),
                    '_id': str(vehicle_data['_id'])
                })
            else:
                print(f"No vehicle data found for ID: {vehicle_obj_id}")

        # Retrieve user data based on the user ID stored in the parking card
        user_id = a.get('user')
        user_data = None
        if user_id:
            try:
                user_obj_id = ObjectId(user_id)
            except Exception as e:
                print(f"Invalid ObjectId for user: {user_id}, Error: {e}")
                user_data = None
            else:
                # Lấy dữ liệu khách hàng
                user_info = conn.nhaxe.user.find_one({'_id': user_obj_id})
                if user_info:
                    user_data = {
                        'full_name': user_info.get('full_name', None),
                        '_id': str(user_info['_id'])
                    }
                else:
                    print(f"No user data found for ID: {user_obj_id}")

        # Tạo obj trả về sau khi lọc dữ liệu
        serialized_dict = {
            "_id": str(a['_id']),
            "id_card": a.get('id_card'),
            "vehicle": vehicles,  # List of vehicles with details
            "vehicle_img": a.get('vehicle_img', ""),
            "user_card": user_data,  # User details (name and _id)
            "user_img": a.get('user_img', ""),   
            "status": a.get('status'),
            "role": a.get('role'),
            "start_date": a.get('start_date', None),
            "end_date": a.get('end_date', None),
            "entrance_time": a.get('entrance_time'),
            "card_fee": a.get('card_fee', 0),
            "created_at": a.get('created_at', None),
            "updated_at": a.get('updated_at', None)
        }

        serialized_list.append(serialized_dict)
    return serialized_list

