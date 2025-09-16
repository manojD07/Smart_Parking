/**
 * Setup file for End-to-End API Tests
 * Configures global test environment and utilities
 */

const axios = require('axios');

// Global test configuration
global.TEST_CONFIG = {
  BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  ADMIN_EMAIL: 'admin@smartparking.com',
  ADMIN_PASSWORD: 'AdminPassword123!',
  TEST_USER_PREFIX: 'e2etest',
  DEFAULT_LOT_ID: '6a650b0d-2311-4b30-a313-ae7529086f11' // Downtown Plaza Parking
};

// Global axios configuration
axios.defaults.baseURL = global.TEST_CONFIG.BASE_URL;
axios.defaults.timeout = global.TEST_CONFIG.TIMEOUT;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Global test utilities
global.TestUtils = {
  /**
   * Generate unique test user data
   */
  generateTestUser: () => {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    return {
      email: `${global.TEST_CONFIG.TEST_USER_PREFIX}_${timestamp}_${random}@example.com`,
      password: 'TestPassword123!',
      first_name: 'Test',
      last_name: 'User',
      phone: `+1${timestamp.toString().slice(-10)}`
    };
  },

  /**
   * Generate test booking data
   */
  generateBookingData: (lotId = global.TEST_CONFIG.DEFAULT_LOT_ID, vehicleType = 'car') => {
    const now = new Date();
    const startTime = new Date(now.getTime() + 24 * 60 * 60 * 1000); // Tomorrow
    const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000); // +2 hours
    const vehicleNumber = `E2E${Math.floor(Math.random() * 1000)}`;

    return {
      lot_id: lotId,
      vehicle_type: vehicleType,
      vehicle_number: vehicleNumber,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString()
    };
  },

  /**
   * Wait for a specified amount of time
   */
  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  /**
   * Validate response structure
   */
  validateResponse: (response, expectedStatus = 200) => {
    expect(response).toBeDefined();
    expect(response.status).toBe(expectedStatus);
    expect(response.data).toBeDefined();
    return response.data;
  },

  /**
   * Validate error response structure
   */
  validateErrorResponse: (error, expectedStatus) => {
    expect(error.response).toBeDefined();
    expect(error.response.status).toBe(expectedStatus);
    expect(error.response.data).toBeDefined();
    expect(error.response.data.message).toBeDefined();
    return error.response.data;
  },

  /**
   * Clean up test data (optional implementation)
   */
  cleanup: async () => {
    // Implementation for cleaning up test data if needed
    console.log('🧹 Test cleanup completed');
  }
};

// Global API client
global.API = {
  auth: {
    register: async (userData) => {
      return axios.post('/api/v1/auth/register', userData);
    },
    
    login: async (credentials) => {
      return axios.post('/api/v1/auth/login', credentials);
    },
    
    refresh: async (refreshToken) => {
      return axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
    }
  },

  parking: {
    getLots: async (token) => {
      return axios.get('/api/v1/parking/lots', {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    
    getLot: async (lotId, token) => {
      return axios.get(`/api/v1/parking/lots/${lotId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    
    getSlots: async (lotId, token, params = {}) => {
      return axios.get(`/api/v1/parking/lots/${lotId}/slots`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
    },
    
    getAvailability: async (lotId, token, params) => {
      return axios.get(`/api/v1/parking/lots/${lotId}/availability`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
    },
    
    searchLots: async (searchData, token) => {
      return axios.post('/api/v1/parking/search', searchData, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  },

  bookings: {
    create: async (bookingData, token) => {
      return axios.post('/api/v1/bookings/', bookingData, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    
    getMyBookings: async (token, params = {}) => {
      return axios.get('/api/v1/bookings/my', {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
    },
    
    getBooking: async (bookingId, token) => {
      return axios.get(`/api/v1/bookings/${bookingId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    
    cancel: async (bookingId, token) => {
      return axios.put(`/api/v1/bookings/${bookingId}/cancel`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    
    getPricingPreview: async (pricingData, token) => {
      return axios.post('/api/v1/bookings/pricing-preview', pricingData, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  }
};

// Test lifecycle hooks
beforeAll(async () => {
  console.log('🚀 Starting End-to-End API Tests...');
  console.log(`📡 Testing against: ${global.TEST_CONFIG.BASE_URL}`);
  
  // Health check
  try {
    const healthResponse = await axios.get('/health');
    console.log('✅ API Health Check: PASSED');
    console.log(`📊 API Status: ${healthResponse.data.status}`);
  } catch (error) {
    console.error('❌ API Health Check: FAILED');
    console.error(`🔥 Error: ${error.message}`);
    throw new Error('API is not available. Please ensure the backend is running.');
  }
});

afterAll(async () => {
  console.log('🏁 End-to-End API Tests completed');
  await global.TestUtils.cleanup();
});

// Global error handler for axios
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNREFUSED') {
      console.error('❌ Connection refused. Is the API server running?');
    }
    return Promise.reject(error);
  }
);

console.log('🔧 Test setup configuration loaded');
