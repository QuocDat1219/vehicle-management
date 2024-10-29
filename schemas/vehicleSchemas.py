from config.db import conn
from bson import ObjectId

def vehicleEntity(item) -> dict:
    return {
        "id": str(item['_id']),
        "number_plate": item['number_plate'],
        "created_at": item.get('created_at', None),  # Include created_at field
        "updated_at": item.get('updated_at', None),  # Include created_at field
    }
    
def serializeDict(a) -> dict:
    return {**{i:str(a[i]) for i in a if i=='_id'},**{i:a[i] for i in a if i!='_id'}}

def serializeList(entity) -> list:
    return [serializeDict(a) for a in entity]