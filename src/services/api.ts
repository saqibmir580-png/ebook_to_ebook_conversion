import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for sending cookies with requests
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized error (e.g., redirect to login)
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Upload file for extraction
export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/v1/ocr/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Get upload status and results
export const getUpload = async (uploadId: string) => {
  const response = await api.get(`/api/v1/ocr/view/${uploadId}`);
  return response.data;
};

// Get all uploads for the current user
export const getUserUploads = async () => {
  const response = await api.get('/api/v1/ocr/history');
  return response.data;
};

// Check processing status
export const checkProcessingStatus = async (taskId: string) => {
  try {
    const response = await api.get(`/api/v1/ocr/status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error checking processing status:', error);
    throw error;
  }
};

export interface Project {
  id: number;
  file_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  file_type: string;
  file_size: number;
  page_count?: number;
  image_count?: number;
  formula_count?: number;
  processing_time?: number;
  error_message?: string;
  xml_url?: string;
  html_url?: string;
  epub_url?: string;
  mobi_url?: string;
  json_export_url?: string;
  csv_export_url?: string;
}

export interface DashboardStats {
  totalProjects: number;
  completedProjects: number;
  processingProjects: number;
  failedProjects: number;
  totalFilesProcessed: number;
  totalProcessingTime: number;
}

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Get all projects for current user
  async getProjects(skip = 0, limit = 100): Promise<Project[]> {
    return this.request<Project[]>(`/api/v1/dashboard/uploads?skip=${skip}&limit=${limit}`);
  }

  // Get specific project with download URLs
  async getProject(id: number): Promise<Project> {
    return this.request<Project>(`/api/v1/uploads/${id}`);
  }

  // Get dashboard statistics
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/v1/ocr/stats');
  }

  // Delete project
  async deleteProject(id: number): Promise<void> {
    await this.request(`/api/v1/uploads/${id}`, { method: 'DELETE' });
  }

  // Download file
  async downloadFile(url: string, filename: string): Promise<void> {
    const token = localStorage.getItem('access_token');
    const response = await fetch(url, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Export project data by calling the backend
  async exportProject(projectId: number, format: 'json' | 'csv'): Promise<void> {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/v1/ocr/export/${projectId}?format=${format}`, {
        method: 'POST',
        headers: {
            ...(token && { Authorization: `Bearer ${token}` }),
        },
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }));
        throw new Error(errorData.detail);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get('content-disposition');
    let filename = `export.${format}`;
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch && filenameMatch.length > 1) {
            filename = filenameMatch[1];
        }
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

export const apiService = new ApiService();

export default api;
