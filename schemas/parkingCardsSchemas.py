from config.db import conn
from bson import ObjectId

def parkingcardEntity(item) -> dict:
    
    return {
        "id": str(item['_id']),
        "vehicle": item['vehicle'],
        "user": item['user'],
        "status": item['status'],
        "role": item['role'],
        "entrance_time": item.get['entrance_time', None],
        "created_at": item.get['created_at', None],
        "updated_at": item.get['updated_at', None]
    }

def serializeDict(a) -> dict:
    return {**{i:str(a[i]) for i in a if i=='_id'},**{i:a[i] for i in a if i!='_id'}}

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
                # Ensure user_id is a valid ObjectId
                user_obj_id = ObjectId(user_id)
            except Exception as e:
                print(f"Invalid ObjectId for user: {user_id}, Error: {e}")
                user_data = None
            else:
                # Fetch the user data from the user collection
                user_info = conn.nhaxe.user.find_one({'_id': user_obj_id})
                if user_info:
                    user_data = {
                        'full_name': user_info.get('full_name', None),
                        '_id': str(user_info['_id'])
                    }
                else:
                    print(f"No user data found for ID: {user_obj_id}")

        # Build the serialized dictionary for the parking card
        serialized_dict = {
            "_id": str(a['_id']),
            "vehicle": vehicles,  # List of vehicles with details
            "user": user_data,  # User details (name and _id)
            "status": a.get('status'),
            "role": a.get('role'),
            "entrance_time": a.get('entrance_time', None),
            "created_at": a.get('created_at', None),
            "updated_at": a.get('updated_at', None)
        }

        serialized_list.append(serialized_dict)
    return serialized_list

