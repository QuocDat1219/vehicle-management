def feeVehicleEntity(item) -> dict:
    return {
        "_id": str(item['_id']),
        "vehicle_type": item['vehicle_type'],
        "day_time": item['day_time'],
        "night_time": item['night_time'],
        "fee_normal": item['fee_normal'],
        "fee_night": item['fee_night'],
        "fee_day": item['fee_day'],
        "fee_surcharge": item['fee_surcharge'],
        "created_at": item.get('created_at', None),  # Include created_at field
        "updated_at": item.get('updated_at', None),
    }
    
def serializeDict(a) -> dict:
    return {
        **{i:str(a[i]) for i in a if i=='_id'},
        **{i:a[i] for i in a if i!='_id'}
        }
    
def serializeList(entity) -> list:
    return [serializeDict(a) for a in entity]