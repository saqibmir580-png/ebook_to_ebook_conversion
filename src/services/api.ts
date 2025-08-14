import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig, AxiosProgressEvent } from 'axios';

// Extend the InternalAxiosRequestConfig to include our custom skipAuth property
declare module 'axios' {
  interface InternalAxiosRequestConfig<D = any> extends AxiosRequestConfig<D> {
    skipAuth?: boolean;
  }
}

// Define types for our API responses
export type UploadStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'processed';

export interface UploadResponse {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  status: UploadStatus;
  extracted_text?: string;
  extracted_images?: Array<{
    url: string;
    alt: string;
  }>;
  created_at: string;
  updated_at: string;
  jats_xml?: string; // Raw JATS XML content
  xml_url?: string;  // URL to download the XML file
  html_url?: string; // URL to download the HTML version
  epub_url?: string; // URL to download the EPUB version
  mobi_url?: string; // URL to download the MOBI version
  page_count?: number; // Number of pages in the document
  image_count?: number; // Number of images in the document
  formula_count?: number; // Number of formulas in the document
  error_message?: string; // Error message if processing failed
  processing_time?: number; // Processing time in seconds
}

// Get API URL from environment variable or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies in requests
  timeout: 30000, // 30 seconds default timeout
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Skip adding auth header if skipAuth is true
    if (config.skipAuth) {
      return config;
    }
    
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Add a request interceptor to ensure trailing slashes for API endpoints
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Only modify the URL if it's an API request (not an external URL)
  if (config.url && !config.url.startsWith('http') && !config.url.endsWith('/')) {
    config.url = `${config.url}/`;
  }
  return config;
});

// Add a response interceptor to handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized error
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Uploads a file to the server with progress tracking
 * @param file The file to upload
 * @param onProgress Callback for upload progress events
 * @returns Promise that resolves with the upload response
 */
// Upload a file to the server with progress tracking
// export const uploadFile = async (
//   file: File,
//   onProgress?: (progressEvent: { loaded: number; total?: number }) => void
// ): Promise<UploadResponse> => {
//   // Check if user is authenticated
//   const token = localStorage.getItem('access_token');
//   if (!token) {
//     // Don't redirect here, let the component handle it
//     throw new Error('Not authenticated. Please log in.');
//   }

//   const formData = new FormData();
//   formData.append('file', file);

//   try {
//     const response = await api.post<UploadResponse>('/api/v1/uploads', formData, {
//       headers: {
//         'Content-Type': 'multipart/form-data',
//         'Authorization': `Bearer ${token}` // Ensure token is sent with the request
//       },
//       onUploadProgress: onProgress ? (progressEvent: AxiosProgressEvent) => {
//         onProgress({
//           loaded: progressEvent.loaded,
//           total: progressEvent.total
//         });
//       } : undefined,
//       timeout: 30 * 60 * 1000, // 30 minutes timeout
//     });
//     return response.data;
//   } catch (err) {
//     console.error('File upload error:', err);
    
//     // Type guard to check if error is an AxiosError
//     if (axios.isAxiosError(err)) {
//       if (err.response?.status === 401) {
//         // Clear auth data and let the interceptor handle the redirect
//         localStorage.removeItem('access_token');
//         localStorage.removeItem('refresh_token');
//         throw new Error('Your session has expired. Please log in again.');
//       }
      
//       const errorMessage = err.response?.data?.detail || 
//                          err.response?.data?.message || 
//                          'Failed to upload file. Please try again.';
      
//       throw new Error(errorMessage);
//     }
    
//     // If it's not an Axios error, throw a generic error
//     throw new Error('An unexpected error occurred during file upload.');
//   }
// };
export const uploadFile = async (
  file: File,
  onProgress?: (progressEvent: { loaded: number; total?: number }) => void
): Promise<UploadResponse> => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated. Please log in.');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    // Use the full API path with /api/v1 prefix
    const response = await api.post<UploadResponse>('/api/v1/uploads', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}`
      },
      onUploadProgress: onProgress ? (progressEvent: AxiosProgressEvent) => {
        onProgress({
          loaded: progressEvent.loaded,
          total: progressEvent.total
        });
      } : undefined,
      timeout: 30 * 60 * 1000, // 30 minutes timeout
      withCredentials: true,  // Important for sending cookies
    });
    console.log(response.data);
    return response.data;
  } catch (err) {
    console.error('File upload error:', err);
    
    if (axios.isAxiosError(err)) {
      if (err.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw new Error('Your session has expired. Please log in again.');
      }
      
      const errorMessage = err.response?.data?.detail || 
                         err.response?.data?.message || 
                         'Failed to upload file. Please try again.';
      
      throw new Error(errorMessage);
    }
    
    throw new Error('An unexpected error occurred during file upload.');
  }
};
/**
 * Get the status of a specific upload
 * @param id The upload ID to fetch
 * @returns Promise that resolves with the upload data
 */
export const getUpload = async (id: string): Promise<UploadResponse> => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated. Please log in.');
  }

  try {
    const response = await api.get<UploadResponse>(`/api/v1/uploads/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching upload:', error);
    
    if (error.response?.status === 401) {
      // Clear auth data and let the interceptor handle the redirect
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      throw new Error('Your session has expired. Please log in again.');
    }
    
    const errorMessage = error.response?.data?.detail || 
                       error.response?.data?.message || 
                       error.message || 
                       'Failed to fetch upload status. Please try again.';
    
    throw new Error(errorMessage);
  }
};

/**
 * Gets a list of the current user's uploads
 * @returns Promise that resolves with an array of uploads
 */
export const getUserUploads = async (): Promise<UploadResponse[]> => {
  try {
    const response = await api.get<UploadResponse[]>('/uploads');
    return response.data;
  } catch (error) {
    console.error('Error fetching user uploads:', error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : 'Failed to fetch uploads. Please try again.'
    );
  }
};

/**
 * Deletes an upload by ID
 * @param id The upload ID to delete
 * @returns Promise that resolves when the upload is deleted
 */
export const deleteUpload = async (id: string): Promise<void> => {
  try {
    await api.delete(`/upload/${id}`);
  } catch (error) {
    console.error('Error deleting upload:', error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : 'Failed to delete upload. Please try again.'
    );
  }
};

export default api;
