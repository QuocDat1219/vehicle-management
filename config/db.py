from pymongo import MongoClient
from decouple import config

# Lấy URL kết nối đến MongoDB từ biến môi trường
database = config("DATABASE")

# Kết nối tới MongoDB
try:
    conn = MongoClient(database)
    # Kiểm tra kết nối bằng cách liệt kê danh sách database
    print("Kết nối MongoDB thành công!")
except Exception as e:
    print("Kết nối MongoDB thất bại:", e)
