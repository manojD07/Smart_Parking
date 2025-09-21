"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, parking, bookings, admin, payments, pricing, conflict_resolution, realtime_availability, duration_validation, analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(parking.router, prefix="/parking", tags=["Parking"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration"])
api_router.include_router(conflict_resolution.router, prefix="/conflicts", tags=["Conflict Resolution"])
api_router.include_router(realtime_availability.router, prefix="/realtime", tags=["Real-time Availability"])
api_router.include_router(duration_validation.router, prefix="/duration", tags=["Duration Validation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
