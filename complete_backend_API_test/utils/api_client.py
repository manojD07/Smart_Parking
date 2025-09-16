"""API Client for End-to-End Tests."""

import time
import uuid
from typing import Dict, Any, Optional, List
import requests
import json
from datetime import datetime, timezone, timedelta

from config import config


class APIClient:
    """Smart Parking API client for testing."""
    
    def __init__(self):
        """Initialize the API client."""
        self.base_url = config.api_url
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_auth: bool = False
    ) -> requests.Response:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        request_headers = config.headers.copy()
        
        if headers:
            request_headers.update(headers)
        
        if use_auth and self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers,
                    timeout=config.TEST_TIMEOUT
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == config.MAX_RETRIES - 1:
                    raise e
                time.sleep(config.RETRY_DELAY)
        
        raise Exception("Max retries exceeded")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, use_auth: bool = False) -> requests.Response:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params, use_auth=use_auth)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, use_auth: bool = False) -> requests.Response:
        """Make POST request."""
        return self._make_request("POST", endpoint, data=data, use_auth=use_auth)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, use_auth: bool = False) -> requests.Response:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, data=data, use_auth=use_auth)
    
    def delete(self, endpoint: str, use_auth: bool = False) -> requests.Response:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, use_auth=use_auth)
    
    # Authentication Methods
    
    def register_user(self, email: str, password: str, first_name: str, last_name: str, phone: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone
        }
        response = self.post("/auth/register", data)
        return response.json()
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and store tokens."""
        data = {
            "email": email,
            "password": password
        }
        response = self.post("/auth/login", data)
        result = response.json()
        
        if response.status_code == 200:
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            if "user" in result:
                self.user_id = result["user"].get("id")
        
        return result
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token."""
        data = {"refresh_token": self.refresh_token}
        response = self.post("/auth/refresh", data)
        result = response.json()
        
        if response.status_code == 200:
            self.access_token = result.get("access_token")
        
        return result
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        response = self.post("/auth/change-password", data, use_auth=True)
        return response.json()
    
    def logout(self) -> Dict[str, Any]:
        """Logout user."""
        response = self.post("/auth/logout", use_auth=True)
        return response.json()
    
    def get_current_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        response = self.get("/auth/me", use_auth=True)
        return response.json()
    
    # Parking Lot Methods
    
    def get_parking_lots(self, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Get list of parking lots."""
        params = {"skip": skip, "limit": limit}
        response = self.get("/parking/lots", params=params)
        return response.json()
    
    def get_parking_lot(self, lot_id: str) -> Dict[str, Any]:
        """Get specific parking lot details."""
        response = self.get(f"/parking/lots/{lot_id}")
        return response.json()
    
    def get_lot_slots(self, lot_id: str, vehicle_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get parking lot slots."""
        params = {"limit": limit}
        if vehicle_type:
            params["vehicle_type"] = vehicle_type
        response = self.get(f"/parking/lots/{lot_id}/slots", params=params)
        return response.json()
    
    def get_lot_availability(self, lot_id: str, vehicle_type: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Get parking lot availability."""
        params = {
            "vehicle_type": vehicle_type,
            "start_time": start_time,
            "end_time": end_time
        }
        response = self.get(f"/parking/lots/{lot_id}/availability", params=params)
        return response.json()
    
    def search_parking_lots(self, latitude: float, longitude: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """Search parking lots by location."""
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km
        }
        response = self.post("/parking/search", data)
        return response.json()
    
    def check_lot_availability_post(
        self, 
        lot_id: str, 
        vehicle_type: str, 
        start_time: str, 
        end_time: str
    ) -> Dict[str, Any]:
        """Check parking lot availability using POST method."""
        data = {
            "vehicle_type": vehicle_type,
            "start_time": start_time,
            "end_time": end_time
        }
        response = self.post(f"/parking/lots/{lot_id}/availability", data)
        return response.json()
    
    def update_parking_lot(self, lot_id: str, lot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update parking lot (admin only)."""
        response = self.put(f"/parking/admin/lots/{lot_id}", lot_data, use_auth=True)
        return response.json()
    
    def delete_parking_lot(self, lot_id: str) -> Dict[str, Any]:
        """Delete parking lot (admin only)."""
        response = self.delete(f"/parking/admin/lots/{lot_id}", use_auth=True)
        return response.json()
    
    # Booking Methods
    
    def create_booking(
        self, 
        lot_id: str, 
        vehicle_type: str, 
        vehicle_number: str, 
        start_time: str, 
        end_time: str
    ) -> Dict[str, Any]:
        """Create a new booking."""
        data = {
            "lot_id": lot_id,
            "vehicle_type": vehicle_type,
            "vehicle_number": vehicle_number,
            "start_time": start_time,
            "end_time": end_time
        }
        response = self.post("/bookings/", data, use_auth=True)
        return response.json()
    
    def get_my_bookings(self, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get current user's bookings."""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        response = self.get("/bookings/my", params=params, use_auth=True)
        return response.json()
    
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """Get specific booking details."""
        response = self.get(f"/bookings/{booking_id}", use_auth=True)
        return response.json()
    
    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """Cancel a booking."""
        response = self.put(f"/bookings/{booking_id}/cancel", use_auth=True)
        return response.json()
    
    def get_pricing_preview(
        self, 
        lot_id: str, 
        vehicle_type: str, 
        start_time: str, 
        end_time: str
    ) -> Dict[str, Any]:
        """Get pricing preview for booking."""
        data = {
            "lot_id": lot_id,
            "vehicle_type": vehicle_type,
            "start_time": start_time,
            "end_time": end_time
        }
        response = self.post("/bookings/pricing-preview", data, use_auth=True)
        return response.json()
    
    def checkin_booking(self, booking_id: str) -> Dict[str, Any]:
        """Check in to a booking."""
        response = self.post(f"/bookings/{booking_id}/checkin", use_auth=True)
        return response.json()
    
    def checkout_booking(self, booking_id: str) -> Dict[str, Any]:
        """Check out from a booking."""
        response = self.post(f"/bookings/{booking_id}/checkout", use_auth=True)
        return response.json()
    
    def get_booking_by_reference(self, booking_reference: str) -> Dict[str, Any]:
        """Get booking by reference code."""
        response = self.get(f"/bookings/reference/{booking_reference}", use_auth=True)
        return response.json()
    
    def search_bookings(
        self, 
        lot_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search bookings with filters."""
        params = {"skip": skip, "limit": limit}
        if lot_id:
            params["lot_id"] = lot_id
        if status:
            params["status"] = status
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self.get("/bookings/search", params=params, use_auth=True)
        return response.json()
    
    # Admin Methods
    
    def create_parking_lot(self, lot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new parking lot (admin only)."""
        response = self.post("/parking/admin/lots", lot_data, use_auth=True)
        return response.json()
    
    def get_lot_statistics(self, lot_id: str) -> Dict[str, Any]:
        """Get parking lot statistics (admin only)."""
        response = self.get(f"/parking/admin/lots/{lot_id}/statistics", use_auth=True)
        return response.json()
    
    # User Management Methods
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        response = self.get("/users/me", use_auth=True)
        return response.json()
    
    def update_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update current user profile."""
        response = self.put("/users/me", profile_data, use_auth=True)
        return response.json()
    
    def change_user_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password via users endpoint."""
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        response = self.post("/users/me/change-password", data, use_auth=True)
        return response.json()
    
    def delete_user_account(self) -> Dict[str, Any]:
        """Delete current user account."""
        response = self.delete("/users/me", use_auth=True)
        return response.json()
    
    def get_user_bookings(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get current user's bookings via users endpoint."""
        params = {"skip": skip, "limit": limit}
        response = self.get("/users/me/bookings", params=params, use_auth=True)
        return response.json()
    
    # Admin User Management Methods
    
    def get_all_users(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all users (admin only)."""
        params = {"skip": skip, "limit": limit}
        response = self.get("/users/", params=params, use_auth=True)
        return response.json()
    
    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID (admin only)."""
        response = self.get(f"/users/{user_id}", use_auth=True)
        return response.json()
    
    def update_user_by_id(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user by ID (admin only)."""
        response = self.put(f"/users/{user_id}", user_data, use_auth=True)
        return response.json()
    
    def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Activate user (admin only)."""
        response = self.post(f"/users/{user_id}/activate", use_auth=True)
        return response.json()
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate user (admin only)."""
        response = self.post(f"/users/{user_id}/deactivate", use_auth=True)
        return response.json()
    
    def make_user_admin(self, user_id: str) -> Dict[str, Any]:
        """Make user admin (admin only)."""
        response = self.post(f"/users/{user_id}/make-admin", use_auth=True)
        return response.json()
    
    def remove_user_admin(self, user_id: str) -> Dict[str, Any]:
        """Remove user admin privileges (admin only)."""
        response = self.post(f"/users/{user_id}/remove-admin", use_auth=True)
        return response.json()
    
    def search_users(
        self, 
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_admin: Optional[bool] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search users with filters (admin only)."""
        params = {"skip": skip, "limit": limit}
        if email:
            params["email"] = email
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if is_admin is not None:
            params["is_admin"] = is_admin
        if is_active is not None:
            params["is_active"] = is_active
        
        response = self.get("/users/search", params=params, use_auth=True)
        return response.json()
    
    # Advanced Admin Methods
    
    def get_admin_dashboard(self) -> Dict[str, Any]:
        """Get admin dashboard overview."""
        response = self.get("/admin/dashboard", use_auth=True)
        return response.json()
    
    def get_revenue_report(
        self, 
        start_date: str, 
        end_date: str, 
        lot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get revenue report (admin only)."""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if lot_id:
            params["lot_id"] = lot_id
        
        response = self.get("/admin/reports/revenue", params=params, use_auth=True)
        return response.json()
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics (admin only)."""
        response = self.get("/admin/users/statistics", use_auth=True)
        return response.json()
    
    def cleanup_expired_bookings(self) -> Dict[str, Any]:
        """Cleanup expired bookings (admin only)."""
        response = self.post("/admin/maintenance/cleanup-expired", use_auth=True)
        return response.json()
    
    # Payment Methods
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment."""
        response = self.post("/payments/", payment_data, use_auth=True)
        return response.json()
    
    def process_payment(self, payment_id: str, gateway_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a payment."""
        response = self.post(f"/payments/{payment_id}/process", gateway_data or {}, use_auth=True)
        return response.json()
    
    def get_my_payments(self, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get current user's payments."""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        response = self.get("/payments/my", params=params, use_auth=True)
        return response.json()
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Get payment details."""
        response = self.get(f"/payments/{payment_id}", use_auth=True)
        return response.json()
    
    def get_payment_by_transaction_id(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment by transaction ID."""
        response = self.get(f"/payments/transaction/{transaction_id}", use_auth=True)
        return response.json()
    
    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """Cancel a pending payment."""
        response = self.post(f"/payments/{payment_id}/cancel", use_auth=True)
        return response.json()
    
    def process_refund(self, payment_id: str, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund (admin only)."""
        response = self.post(f"/payments/{payment_id}/refund", refund_data, use_auth=True)
        return response.json()
    
    def get_booking_payments(self, booking_id: str) -> List[Dict[str, Any]]:
        """Get all payments for a booking."""
        response = self.get(f"/payments/booking/{booking_id}", use_auth=True)
        return response.json()
    
    def get_payment_gateway_status(self) -> Dict[str, Any]:
        """Get payment gateway status."""
        response = self.get("/payments/gateway/status", use_auth=True)
        return response.json()
    
    # Payment Card Methods
    
    def add_payment_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a payment card."""
        response = self.post("/payments/cards", card_data, use_auth=True)
        return response.json()
    
    def get_my_payment_cards(self) -> List[Dict[str, Any]]:
        """Get current user's payment cards."""
        response = self.get("/payments/cards", use_auth=True)
        return response.json()
    
    def set_default_card(self, card_id: str) -> Dict[str, Any]:
        """Set a card as default."""
        response = self.post(f"/payments/cards/{card_id}/set-default", use_auth=True)
        return response.json()
    
    def remove_payment_card(self, card_id: str) -> Dict[str, Any]:
        """Remove a payment card."""
        response = self.delete(f"/payments/cards/{card_id}", use_auth=True)
        return response.json()
    
    # Admin Payment Methods
    
    def get_payment_statistics(self, start_date: str, end_date: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get payment statistics (admin only)."""
        params = {"start_date": start_date, "end_date": end_date}
        if user_id:
            params["user_id"] = user_id
        response = self.get("/payments/stats/overview", params=params, use_auth=True)
        return response.json()
    
    def generate_payment_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate payment report (admin only)."""
        response = self.post("/payments/reports/generate", report_data, use_auth=True)
        return response.json()
    
    def get_all_payments(self, skip: int = 0, limit: int = 50, **filters) -> List[Dict[str, Any]]:
        """Get all payments (admin only)."""
        params = {"skip": skip, "limit": limit, **filters}
        response = self.get("/payments/admin/all", params=params, use_auth=True)
        return response.json()
    
    def expire_old_payments(self) -> Dict[str, Any]:
        """Expire old payments (admin only)."""
        response = self.post("/payments/admin/expire-old", use_auth=True)
        return response.json()
    
    # Health Check
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.get("/health")
        return response.json()
    
    # Utility Methods
    
    def generate_future_datetime(self, hours_from_now: int = 1) -> str:
        """Generate future datetime string."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
        return future_time.isoformat()
    
    def generate_unique_email(self, prefix: str = "test") -> str:
        """Generate unique email for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{unique_id}@e2etest.com"
    
    def generate_unique_vehicle_number(self, prefix: str = "TEST") -> str:
        """Generate unique vehicle number."""
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"{prefix}{unique_id}"
    
    def cleanup(self):
        """Cleanup session and tokens."""
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.session.close()
