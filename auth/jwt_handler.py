import time
import jwt
from decouple import config

JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")

#Hàm trả về token được gen
def token_response(token: str):
    return {
       "access_token": token, 
    }
    
def signJWT(userId: str, fullName: str, role: str, username: str):
    payload = {
        "user_id": userId,
        "full_name": fullName,
        "role": role,
        "username": username,
        "expires": time.time() + 43200
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm = JWT_ALGORITHM)
    return token_response(token)

def decodeJWT(token: str):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])       
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
