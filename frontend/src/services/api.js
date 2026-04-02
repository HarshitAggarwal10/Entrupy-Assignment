import axios from 'axios';

// Use backend URL directly - with explicit /api prefix
const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE_URL = BACKEND_URL + '/api';

console.log('API Base URL:', API_BASE_URL); // Debug log

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add a request interceptor to include the JWT token in all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle authentication errors (401)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear local storage and redirect to login if unauthorized
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // If we're not already on a page that handles its own auth, reload
      // This will force App.jsx to re-render and show the Login screen
      if (!window.location.pathname.includes('/login')) {
         window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getToken: () => {
    return localStorage.getItem('token');
  },
};

export const productService = {
  getProducts: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.brand) params.append('brand', filters.brand);
    if (filters.category) params.append('category', filters.category);
    if (filters.source) params.append('source', filters.source);
    if (filters.min_price) params.append('min_price', filters.min_price);
    if (filters.max_price) params.append('max_price', filters.max_price);
    if (filters.skip) params.append('skip', filters.skip);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
    
    return api.get(`/products?${params.toString()}`);
  },

  getProduct: (productId) => {
    return api.get(`/products/${productId}`);
  },

  getPriceHistory: (productId, limit = 50) => {
    return api.get(`/products/${productId}/price-history?limit=${limit}`);
  },

  getAnalytics: () => {
    return api.get('/analytics');
  },

  getStats: () => {
    return api.get('/stats');
  },

  getNotifications: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.is_processed !== undefined) params.append('is_processed', filters.is_processed);
    if (filters.skip) params.append('skip', filters.skip);
    if (filters.limit) params.append('limit', filters.limit);
    
    return api.get(`/notifications?${params.toString()}`);
  },

  refreshData: () => {
    return api.post('/data/refresh');
  },

  processNotifications: () => {
    return api.post('/notifications/process');
  },

  health: () => {
    return api.get('/health');
  },
};

export default api;
