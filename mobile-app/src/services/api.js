import React, { createContext, useContext } from 'react';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

// API Configuration
const API_BASE_URL = __DEV__ 
  ? Constants.expoConfig?.extra?.apiUrl || 'http://localhost:5000/api/v1'
  : Constants.expoConfig?.extra?.apiUrl || 'https://bluespace-restaurants.onrender.com/api/v1';

if (__DEV__) {
  console.log('API Base URL:', API_BASE_URL);
}

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
export const tokenManager = {
  async getToken() {
    try {
      return await SecureStore.getItemAsync('auth_token');
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  },

  async setToken(token) {
    try {
      await SecureStore.setItemAsync('auth_token', token);
    } catch (error) {
      console.error('Error setting token:', error);
    }
  },

  async removeToken() {
    try {
      await SecureStore.deleteItemAsync('auth_token');
    } catch (error) {
      console.error('Error removing token:', error);
    }
  },
};

// Request interceptor to add token
api.interceptors.request.use(
  async (config) => {
    const token = await tokenManager.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Log detailed error information for debugging
    if (error.response) {
      // Server responded with error status
      console.error('API Error Response:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      });
    } else if (error.request) {
      // Request was made but no response received
      console.error('API Network Error:', {
        message: error.message,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: error.config?.baseURL + error.config?.url,
      });
    } else {
      // Something else happened
      console.error('API Error:', error.message);
    }
    
    if (error.response?.status === 401) {
      // Token expired or invalid
      await tokenManager.removeToken();
      // Navigate to login (handled by AuthContext)
    }
    return Promise.reject(error);
  }
);

// API Methods
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.success && response.data.token) {
      await tokenManager.setToken(response.data.token);
    }
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    if (response.data.success && response.data.token) {
      await tokenManager.setToken(response.data.token);
    }
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async () => {
    await tokenManager.removeToken();
    return { success: true };
  },
};

export const ordersAPI = {
  getOrders: async (params = {}) => {
    const response = await api.get('/orders', { params });
    return response.data;
  },

  getOrder: async (orderId) => {
    const response = await api.get(`/orders/${orderId}`);
    return response.data;
  },

  createOrder: async (orderData) => {
    const response = await api.post('/orders', orderData);
    return response.data;
  },

  createGuestOrder: async (orderData) => {
    const response = await api.post('/orders/guest', orderData);
    return response.data;
  },

  trackOrder: async (orderId) => {
    const response = await api.get(`/orders/${orderId}/track`);
    return response.data;
  },

  updateOrderStatus: async (orderId, status) => {
    const response = await api.put(`/orders/${orderId}/status`, { status });
    return response.data;
  },

  cancelOrder: async (orderId) => {
    const response = await api.delete(`/orders/${orderId}`);
    return response.data;
  },
};

export const menuAPI = {
  getMenuItems: async (restaurantId, categoryId = null) => {
    const params = { restaurant_id: restaurantId };
    if (categoryId) params.category_id = categoryId;
    const response = await api.get('/menu/items', { params });
    return response.data;
  },

  getMenuItem: async (itemId) => {
    const response = await api.get(`/menu/items/${itemId}`);
    return response.data;
  },

  createMenuItem: async (itemData) => {
    const response = await api.post('/menu/items', itemData);
    return response.data;
  },

  updateMenuItem: async (itemId, itemData) => {
    const response = await api.put(`/menu/items/${itemId}`, itemData);
    return response.data;
  },

  deleteMenuItem: async (itemId) => {
    const response = await api.delete(`/menu/items/${itemId}`);
    return response.data;
  },

  getCategories: async (restaurantId) => {
    const response = await api.get('/menu/categories', {
      params: { restaurant_id: restaurantId },
    });
    return response.data;
  },
};

export const paymentsAPI = {
  processPayment: async (orderId, paymentMethod) => {
    const response = await api.post('/payments/process', {
      order_id: orderId,
      payment_method: paymentMethod,
    });
    return response.data;
  },

  confirmPayment: async (orderId) => {
    const response = await api.post(`/payments/confirm/${orderId}`);
    return response.data;
  },

  getPaymentStatus: async (orderId) => {
    const response = await api.get(`/payments/status/${orderId}`);
    return response.data;
  },
};

export const restaurantsAPI = {
  listRestaurants: async () => {
    const response = await api.get('/restaurants');
    return response.data;
  },

  getMyRestaurant: async () => {
    const response = await api.get('/restaurants/me');
    return response.data;
  },

  updateMyRestaurant: async (restaurantData) => {
    const response = await api.put('/restaurants/me', restaurantData);
    return response.data;
  },

  getRestaurant: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}`);
    return response.data;
  },
};

export const analyticsAPI = {
  getDashboardStats: async (days = 7) => {
    const response = await api.get('/analytics/dashboard', {
      params: { days },
    });
    return response.data;
  },

  getRevenueStats: async (days = 30) => {
    const response = await api.get('/analytics/revenue', {
      params: { days },
    });
    return response.data;
  },
};

// API Provider Context
const APIContext = createContext({
  api,
  authAPI,
  ordersAPI,
  menuAPI,
  paymentsAPI,
  restaurantsAPI,
  analyticsAPI,
});

export const APIProvider = ({ children }) => {
  return (
    <APIContext.Provider
      value={{
        api,
        authAPI,
        ordersAPI,
        menuAPI,
        paymentsAPI,
        restaurantsAPI,
        analyticsAPI,
      }}
    >
      {children}
    </APIContext.Provider>
  );
};

export const useAPI = () => useContext(APIContext);

export default api;

