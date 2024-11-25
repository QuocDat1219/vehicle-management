from config.db import conn
from bson import ObjectId

def parkinghistory(item) -> dict:
    return {
        "id": str(item['_id']),
        "vehicle": item['vehicle'],
        "vehicle_img": item['vehicle_img'],
        "user": item['user'],
        "user_img": item['user_img'],
        "parkingcard": item['parkingcard'],
        "status": item['status'],
        "entrance_time": item.get['entrance_time', None],  
        "exit_time": item.get['exit_time', None],
        "fee": item['fee'],    
        "time_at": item.get['updated_at', None]
    }


def serializeDict(a) -> dict:
    return {**{i:str(a[i]) for i in a if i=='_id'},**{i:a[i] for i in a if i!='_id'}}

def serializeDetail(item) -> dict:
    """
    Serialize a single parking history document with detailed information
    about vehicle (stored as string) and user.
    """
    # Retrieve vehicle details
    vehicle_id = item.get('vehicle')  # Single string ID
    vehicle_data = None
    if vehicle_id:
        try:
            vehicle_obj_id = ObjectId(vehicle_id)  # Convert to ObjectId
            vehicle_data = conn.nhaxe.vehicle.find_one({'_id': vehicle_obj_id})
            if vehicle_data:
                vehicle_data = {
                    'number_plate': vehicle_data.get('number_plate', None),
                    'vehicle_type': vehicle_data.get('vehicle_type', None),
                    '_id': str(vehicle_data['_id'])
                }
            else:
                print(f"No vehicle data found for ID: {vehicle_obj_id}")
        except Exception as e:
            print(f"Invalid ObjectId for vehicle: {vehicle_id}, Error: {e}")

    # Retrieve user details
    user_id = item.get('user')
    user_data = None
    if user_id:
        try:
            user_obj_id = ObjectId(user_id)  # Convert to ObjectId
            user_info = conn.nhaxe.user.find_one({'_id': user_obj_id})
            if user_info:
                user_data = {
                    'full_name': user_info.get('full_name', None),
                    'phone': user_info.get('phone', None),
                    '_id': str(user_info['_id'])
                }
            else:
                print(f"No user data found for ID: {user_obj_id}")
        except Exception as e:
            print(f"Invalid ObjectId for user: {user_id}, Error: {e}")

    card_id = item.get('parkingcard')
    card_data = None
    if card_id:
        try:
            card_obj_id = ObjectId(card_id)  # Convert to ObjectId
            card_info = conn.nhaxe.parkingcard.find_one({'_id': card_obj_id})
            if card_obj_id:
                card_data = {
                    'id_card': card_info.get('id_card', None),
                    'role': card_info.get('role', None),
                    '_id': str(card_info['_id'])
                }
            else:
                print(f"No vehicle data found for ID: {card_obj_id}")
        except Exception as e:
            print(f"Invalid ObjectId for user: {card_id}, Error: {e}")
            
    # Build the serialized dictionary
    serialized_data = {
        "_id": str(item['_id']),
        "vehicle": vehicle_data,  # Single vehicle detail
        "vehicle_img": item.get("vehicle_img"),
        "vehicle_img_in": item.get("vehicle_img_in"),
        "user": user_data,  # User details
        "user_img": item.get("user_img"),
        "user_img_in": item.get("user_img_in"),
        "parkingcard": card_data,
        "status": item.get('status'),
        "entrance_time": item.get('entrance_time', None),
        "exit_time": item.get('exit_time', None),
        "fee": item.get('fee', 0),
        "time_at": item.get('time_at', None),
    }

    return serialized_data


def serializeList(entity) -> list:
    """
    Serialize a list of parking history documents.
    Each document contains vehicle (stored as string) and user details.
    """
    serialized_list = []
    for item in entity:
        serialized_list.append(serializeDetail(item))
    return serialized_list