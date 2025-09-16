# Smart Parking Management System - Postman Collection

This directory contains a comprehensive Postman collection for testing all the Smart Parking Management System APIs.

## 📁 Files Included

- **`Smart_Parking_API.postman_collection.json`** - Main collection with all API endpoints
- **`Smart_Parking_Local.postman_environment.json`** - Local development environment
- **`Smart_Parking_Production.postman_environment.json`** - Production environment template
- **`README.md`** - This documentation file

## 🚀 Quick Start

### 1. Import Collections

1. Open Postman
2. Click **Import** button
3. Drag and drop or select the collection file: `Smart_Parking_API.postman_collection.json`
4. Import the environment files:
   - `Smart_Parking_Local.postman_environment.json`
   - `Smart_Parking_Production.postman_environment.json`

### 2. Select Environment

- For local development: Select **"Smart Parking - Local Development"** environment
- For production testing: Select **"Smart Parking - Production"** environment

### 3. Start Testing

1. **Health Check**: Start with the health check endpoint to verify API connectivity
2. **Register**: Create a new user account
3. **Login**: Get authentication tokens
4. **Explore**: Use other endpoints (tokens are automatically managed)

## 📋 Collection Structure

### 🏥 Health Check
- **GET** `/health` - Check API health status

### 🔐 Authentication
- **POST** `/api/v1/auth/register` - Register new user
- **POST** `/api/v1/auth/login` - User login
- **POST** `/api/v1/auth/refresh` - Refresh access token
- **GET** `/api/v1/auth/me` - Get current user info
- **POST** `/api/v1/auth/change-password` - Change password
- **POST** `/api/v1/auth/logout` - User logout

### 👤 User Management

#### Current User Operations
- **GET** `/api/v1/users/me` - Get current user profile
- **PUT** `/api/v1/users/me` - Update current user profile
- **POST** `/api/v1/users/me/change-password` - Change password
- **DELETE** `/api/v1/users/me` - Deactivate account
- **GET** `/api/v1/users/me/bookings` - Get user's bookings

#### Admin User Management (Requires Admin Rights)
- **GET** `/api/v1/users/` - Get all users
- **GET** `/api/v1/users/{user_id}` - Get user by ID
- **PUT** `/api/v1/users/{user_id}` - Update user
- **POST** `/api/v1/users/{user_id}/activate` - Activate user
- **POST** `/api/v1/users/{user_id}/deactivate` - Deactivate user
- **POST** `/api/v1/users/{user_id}/make-admin` - Grant admin privileges
- **POST** `/api/v1/users/{user_id}/remove-admin` - Remove admin privileges
- **GET** `/api/v1/users/search` - Search users

### 🅿️ Parking Management

#### Parking Lots
- **GET** `/api/v1/parking/lots` - Get all parking lots
- **GET** `/api/v1/parking/lots/{lot_id}` - Get parking lot details
- **GET** `/api/v1/parking/lots/{lot_id}/availability` - Check availability
- **GET** `/api/v1/parking/lots/{lot_id}/slots` - Get parking slots
- **POST** `/api/v1/parking/lots/{lot_id}/availability` - Check specific availability

#### Search & Discovery
- **POST** `/api/v1/parking/search` - Search parking lots by location

#### Admin Parking Management (Requires Admin Rights)
- **POST** `/api/v1/parking/admin/lots` - Create parking lot
- **PUT** `/api/v1/parking/admin/lots/{lot_id}` - Update parking lot
- **DELETE** `/api/v1/parking/admin/lots/{lot_id}` - Delete parking lot
- **GET** `/api/v1/parking/admin/lots/{lot_id}/statistics` - Get lot statistics

### 📅 Booking Management
- **POST** `/api/v1/bookings/` - Create booking
- **GET** `/api/v1/bookings/my` - Get user's bookings
- **GET** `/api/v1/bookings/{booking_id}` - Get booking details
- **GET** `/api/v1/bookings/reference/{booking_reference}` - Get booking by reference
- **PUT** `/api/v1/bookings/{booking_id}/cancel` - Cancel booking
- **POST** `/api/v1/bookings/{booking_id}/checkin` - Check in
- **POST** `/api/v1/bookings/{booking_id}/checkout` - Check out
- **POST** `/api/v1/bookings/pricing-preview` - Get pricing preview
- **GET** `/api/v1/bookings/search` - Search bookings

### 🔧 Administration (Requires Admin Rights)
- **GET** `/api/v1/admin/dashboard` - Admin dashboard
- **GET** `/api/v1/admin/reports/revenue` - Revenue reports
- **GET** `/api/v1/admin/users/statistics` - User statistics
- **POST** `/api/v1/admin/maintenance/cleanup-expired` - Cleanup expired bookings

## 🔧 Environment Variables

### Automatically Managed Variables
These are set automatically by test scripts:
- `access_token` - JWT access token (set after login)
- `refresh_token` - JWT refresh token (set after login)
- `user_id` - Current user ID (set after registration/login)
- `booking_id` - Sample booking ID (set after creating booking)
- `booking_reference` - Booking reference number
- `lot_id` - Sample parking lot ID

### Manual Configuration Variables
- `base_url` - API base URL (http://localhost:8000 for local)
- `admin_email` - Admin user email
- `admin_password` - Admin user password
- `test_user_email` - Test user email
- `test_user_password` - Test user password

## 🔄 Testing Workflow

### For Regular Users:
1. **Register** → **Login** → **Search Parking** → **Create Booking** → **Check In/Out** → **Cancel**

### For Admin Users:
1. **Login as Admin** → **Create Parking Lots** → **Manage Users** → **View Reports** → **Maintenance**

## ✨ Features

### Automatic Token Management
- Login requests automatically save tokens to environment variables
- Subsequent requests automatically include authorization headers
- Refresh token workflow included

### Smart Test Scripts
- Automatic variable extraction from responses
- Response time logging
- Error handling and logging
- Response validation

### Pre-request Scripts
- Automatic timestamp addition
- Authorization header injection
- Request logging

### Environment Support
- Local development environment (localhost:8000)
- Production environment template
- Easy environment switching

## 🛠️ Advanced Usage

### Running Collection Tests
```javascript
// Run entire collection
pm.collection.run("Smart Parking Management System API");

// Run specific folder
pm.collection.run("Authentication");
```

### Custom Pre-request Scripts
```javascript
// Add custom headers
pm.request.headers.add({
  key: 'X-Client-Version',
  value: '1.0.0'
});

// Generate test data
pm.environment.set('random_email', 
  'user' + Math.floor(Math.random() * 1000) + '@example.com'
);
```

### Custom Test Scripts
```javascript
// Validate response structure
pm.test("Response has correct structure", function () {
  const response = pm.response.json();
  pm.expect(response).to.have.property('id');
  pm.expect(response).to.have.property('created_at');
});

// Performance testing
pm.test("Response time is less than 1000ms", function () {
  pm.expect(pm.response.responseTime).to.be.below(1000);
});
```

## 🔍 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Solution: Login first to get access token
   - Check if token is expired (use refresh endpoint)

2. **403 Forbidden**
   - Solution: Ensure you have admin privileges for admin endpoints
   - Contact admin to grant necessary permissions

3. **404 Not Found**
   - Solution: Check if the resource (user, booking, lot) exists
   - Verify the ID in the URL path

4. **422 Validation Error**
   - Solution: Check request body format and required fields
   - Verify data types and constraints

### Debug Tips

1. **Check Environment Variables**: Ensure correct environment is selected
2. **View Console**: Check Postman console for detailed logs
3. **Validate JSON**: Ensure request bodies are valid JSON
4. **Check Base URL**: Verify the API server is running on the correct port

## 📖 API Documentation

For detailed API documentation, visit:
- **Local**: http://localhost:8000/docs (Swagger UI)
- **Local**: http://localhost:8000/redoc (ReDoc)
- **Production**: https://api.smartparking.com/docs

## 🔐 Security Notes

- Never commit real credentials to version control
- Use environment variables for sensitive data
- Rotate API keys and passwords regularly
- Use HTTPS in production environments

## 📝 Request Examples

### Sample Registration Request
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

### Sample Booking Request
```json
{
  "lot_id": "550e8400-e29b-41d4-a716-446655440000",
  "vehicle_type": "car",
  "vehicle_number": "ABC123",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T12:00:00Z",
  "notes": "Business meeting parking"
}
```

### Sample Parking Lot Search
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_km": 5.0,
  "vehicle_type": "car",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T12:00:00Z"
}
```

## 📞 Support

For API support and questions:
- Check the API documentation at `/docs`
- Review error messages and status codes
- Use the health check endpoint to verify connectivity
- Check server logs for detailed error information

---

**Happy Testing! 🚀**
