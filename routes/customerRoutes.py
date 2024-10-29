from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from model.customerModel import Customer
from config.db import conn
from schemas.customerSchemas import serializeDict, serializeList
from bson import ObjectId
from auth.jwt_handler import signJWT
from passlib.context import CryptContext
from pydantic import BaseModel
from auth.jwt_bearer import jwtBearer

customerRoutes = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Login model
class LoginModel(BaseModel):
    username: str
    password: str

# Model cho đổi mật khẩu
class ChangePasswordModel(BaseModel):
    old_password: str
    new_password: str
    
# Hash password function
def hash_password(password:str) -> str:
    return pwd_context.hash(password)

# Verify password function
def verify_password(plain_password:str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)    

@customerRoutes.post("/api/customer/create", dependencies=[Depends(jwtBearer())])
def create_New_User(cus: Customer):
    try:
        if conn.nhaxe.customer.find_one({"username": cus.username}):
            return HTTPException(status_code=400, detail={"msg": "Tài khoản đã được sử dụng"})
        
        # Mã hóa password
        hashed_password = hash_password(cus.password)
        cus.password = hashed_password

        # Thêm trường created_at
        cus_dict = dict(cus)
        cus_dict["created_at"] = datetime.utcnow()

        created_user = conn.nhaxe.customer.insert_one(cus_dict)
        if created_user:
            return HTTPException(status_code = 200, detail={"msg": "success", "data": serializeList(conn.nhaxe.customer.find())})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Không thể tạo người dùng mới", "error": str(e)})

#Lấy danh sách tài khoản
@customerRoutes.get("/api/customer/", dependencies=[Depends(jwtBearer())])
def get_all_customer():
    try:
        # Tìm tất cả người dùng không phải là admin và không lấy trường mật khẩu
        user_list = serializeList(conn.nhaxe.customer.find())

        if not user_list:
            return []

        return serializeList(user_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Lấy danh sách tài khoản
@customerRoutes.get("/api/customer/{id}", dependencies=[Depends(jwtBearer())])
def get_all_customer(id):
    try:
        user = conn.nhaxe.customer.find_one({"_id": ObjectId(id)})
        print(user)
        if not user:
            return []
        return serializeDict(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Đăng nhập người dùng
@customerRoutes.post("/api/customer/login")
def login_customer(customer: LoginModel):
    try:
        # Tìm người dùng theo username
        db_customer = conn.nhaxe.customer.find_one({"username": customer.username})
        role =  db_customer["role"]
        if not db_customer:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        
        # Kiểm tra mật khẩu
        if not verify_password(customer.password, db_customer["password"]):
            raise HTTPException(status_code=401, detail="Sai mật khẩu")
        
        # Tạo JWT token
        token = signJWT(str(db_customer["_id"]), db_customer["fullname"], db_customer["role"], db_customer["username"])
        return {"access_token": token.get("access_token"), "role": role}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Sai tên tài khoản hoặc mật khẩu", "error": str(e)})
    
# Đổi mật khẩu
@customerRoutes.put("/api/customer/change-password", dependencies=[Depends(jwtBearer())])
async def change_password(change_password_model: ChangePasswordModel, token: str = Depends(jwtBearer())):
    user_id = token["user_id"]
    if not token:
        raise HTTPException(status_code=403, detail="Token không hợp lệ hoặc đã hết hạn!")
    
    db_customer = conn.nhaxe.customer.find_one({"_id": ObjectId(user_id)})
    if not db_customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    
    if not verify_password(change_password_model.old_password, db_customer["password"]):
        raise HTTPException(status_code=401, detail="Mật khẩu cũ không đúng")
    
    new_hashed_password = hash_password(change_password_model.new_password)
    conn.nhaxe.customer.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": new_hashed_password}})
    
    return HTTPException(status_code=200,detail={"msg": "Đổi mật khẩu thành công"})


# Reset mật khẩu
@customerRoutes.put("/api/customer/reset-password/{id}", dependencies=[Depends(jwtBearer())])
async def reset_password(id, token: str = Depends(jwtBearer())):
    try:
        if token["role"] != "admin":
            raise HTTPException(status_code = 403, detail = "Bạn không có quyền đặt lại mật khẩu!")
         # Tìm người dùng theo user_id
        db_customer = conn.nhaxe.customer.find_one({"_id": ObjectId(id)})
        if not db_customer:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        new_hashed_password = hash_password("vnptvlg")
        conn.nhaxe.customer.update_one({"_id": ObjectId(id)}, {"$set": {"password": new_hashed_password}})
        return HTTPException(status_code = 200, detail = {"msg": "Đặt lại mật khẩu thành công"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Không thể đặt lại mật khẩu", "error": str(e)})

#Thay đổi quyền người dùng
# Model để thay đổi quyền
class ChangeRoleModel(BaseModel):
    role: str
    fullname: str

# API để thay đổi quyền người dùng
@customerRoutes.put("/api/customer/edit/{user_id}", dependencies=[Depends(jwtBearer())])
async def change_customer_role(user_id: str, change_role_model: ChangeRoleModel, token: str = Depends(jwtBearer())):
    try:
        # Kiểm tra quyền hiện tại của người dùng
        if token["role"] != "admin":
            raise HTTPException(status_code=403, detail="Bạn không có quyền thay đổi quyền của người dùng khác")
        
        # Tìm người dùng theo user_id
        db_customer = conn.nhaxe.customer.find_one({"_id": ObjectId(user_id)})
        if not db_customer:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

        # Chỉ cho phép thay đổi thành các quyền hợp lệ
        valid_roles = ["admin", "user bras", "user gpon"]
        if change_role_model.role not in valid_roles:
            raise HTTPException(status_code=400, detail="Quyền không hợp lệ")
        
        # Cập nhật quyền của người dùng
        updated_role = conn.nhaxe.customer.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": 
                {"role": change_role_model.role, "fullname": change_role_model.fullname}})
        
        if updated_role.modified_count == 0:
            raise HTTPException(status_code = 404, detail = {"msg": "Không tìm thấy người dùng này"})
        return HTTPException(status_code=200, detail={"msg": "Thay đổi quyền thành công", "data": serializeList(conn.nhaxe.customer.find())})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Không thể thay đổi quyền", "error": str(e)})
        
@customerRoutes.patch("/api/customer/edit/{id}", dependencies=[Depends(jwtBearer())])
async def edit_customerInfo(id: str, fullname: str = Query(...)):
    try:
        # Cập nhật thông tin fullname cho user với id tương ứng
        updated_customer = conn.nhaxe.customer.update_one(
            {"_id": ObjectId(id)}, 
            {"$set": {"fullname": fullname}}
        )

        # Kiểm tra xem có bất kỳ tài liệu nào được cập nhật hay không
        if updated_customer.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản hoặc không có thay đổi")

        return {"msg": "Thay đổi thông tin thành công"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": "Không thể thay đổi thông tin cá nhân", "error": str(e)})
    

    #Xoa tai khoan
@customerRoutes.delete("/api/customer/{id}", dependencies=[Depends(jwtBearer())])
def delete_customer(id):
    try:
        deleted_customer = conn.nhaxe.customer.delete_one({"_id": ObjectId(id)})
        
        if deleted_customer.deleted_count == 1:
            return HTTPException(status_code = 200, detail = {"msg":"success", "data": serializeList(conn.nhaxe.customer.find())})
        else:
            return HTTPException(status_code=500, detail={"msg": "error"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
