from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from decouple import config

from routes.userRoutes import userRoutes
from routes.parkingCardsRoutes import parkingCardRoutes
from routes.vehicleRoutes import vehicleRoutes
from routes.customerRoutes import customerRoutes
from service.vehicleDetectionService import vehicleDetectionRoutes 
from routes.feeRoutes import feeRoutes
from routes.parkingHistoryRoutes import ParkingHistoryRoutes

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(userRoutes)
app.include_router(parkingCardRoutes)
app.include_router(vehicleRoutes)
app.include_router(customerRoutes)
app.include_router(vehicleDetectionRoutes)
app.include_router(feeRoutes)
app.include_router(ParkingHistoryRoutes)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=int(config('PORT')), reload=True)

