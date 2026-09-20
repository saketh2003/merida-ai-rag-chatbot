import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Authorization JWT token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth endpoints
export const authApi = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  register: async (email, password, fullName) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Chat & Conversation endpoints
export const chatApi = {
  listConversations: async () => {
    const response = await api.get('/chat/conversations');
    return response.data;
  },
  createConversation: async (title = 'New Conversation') => {
    const response = await api.post('/chat/conversations', { title });
    return response.data;
  },
  getConversation: async (id) => {
    const response = await api.get(`/chat/conversations/${id}`);
    return response.data;
  },
  deleteConversation: async (id) => {
    const response = await api.delete(`/chat/conversations/${id}`);
    return response.data;
  },
  sendMessage: async (conversationId, prompt) => {
    const response = await api.post(`/chat/conversations/${conversationId}/message`, {
      prompt,
    });
    return response.data;
  },
};

// Admin Knowledge Base endpoints
export const kbApi = {
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/kb/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  listDocuments: async () => {
    const response = await api.get('/admin/kb/documents');
    return response.data;
  },
  deleteDocument: async (id) => {
    const response = await api.delete(`/admin/kb/documents/${id}`);
    return response.data;
  },
};

export default api;
