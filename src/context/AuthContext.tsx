import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';
interface User {
  email: string;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean }>;
  register: (fullName: string, email: string, password: string, confirmPassword: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Export the context itself for direct usage if needed
export { AuthContext };

const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchUserData = async (token: string) => {
    try {
      // Set the token in localStorage for the API service
      localStorage.setItem('access_token', token);
      
      // Use the API service to make the request
      const response = await api.get('/api/v1/auth/me');
      const userData = response.data;

      setUser({
        email: userData.email,
        full_name: userData.full_name || userData.email
      });
      setIsAuthenticated(true);
      return userData;
    } catch (error) {
      console.error('Error fetching user data:', error);
      // Clear tokens on error
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Check authentication status on initial load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await fetchUserData(token);
        } catch (error) {
          console.error('Authentication check failed:', error);
        }
      } else {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      // Use the API service to make the login request
      const response = await api.post(
        '/api/v1/auth/login',
        new URLSearchParams({
          username: email,
          password: password,
          grant_type: 'password'
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          // @ts-ignore - skipAuth is a custom property we've added to the Axios config
          skipAuth: true // Skip auth for login
        }
      );

      const responseData = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', responseData.access_token);
      localStorage.setItem('refresh_token', responseData.refresh_token);

      // Fetch and set user data
      await fetchUserData(responseData.access_token);
      
      toast.success('Login successful!', {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
      
      return { success: true };
    } catch (error: any) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to login. Please check your credentials.';
      toast.error(errorMessage, {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
      return { success: false };
    } finally {
      setLoading(false);
    }
  };

  const register = async (fullName: string, email: string, password: string, confirmPassword: string) => {
    setLoading(true);
    try {
      // Register the user using the API service
      const response = await api.post(
        '/api/v1/auth/register',
        {
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword
        },
        {
          // @ts-ignore - skipAuth is a custom property we've added to the Axios config
          skipAuth: true, // Skip auth for registration
          headers: {
            'Content-Type': 'application/json'
          }
        } as any // Cast to any to bypass TypeScript error
      );

      if (response.status >= 400) {
        const errorMessage = response.data.detail || 'Failed to register';
        toast.error(errorMessage, {
          position: "top-right",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
          progress: undefined,
        });
        throw new Error(errorMessage);
      }

      toast.success('Registration successful!', {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });

      return { success: true };
    } catch (error) {
      if (error instanceof Error) {
        return { success: false, error: error.message };
      }
      return { success: false, error: 'An unknown error occurred' };
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<{ success: boolean }> => {
    try {
      setLoading(true);
      
      // Call the logout endpoint if it exists
      try {
        // @ts-ignore - skipAuth is a custom property we've added to the Axios config
        await api.post('/api/v1/auth/logout', {}, { skipAuth: true } as any);
      } catch (error) {
        // Log but don't show error to user - we'll still clear local storage
        console.log('Logout API call failed, proceeding with local logout');
      }
      
      // Clear all auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      
      // Show success toast
      toast.success('You have been logged out successfully!', {
        position: 'top-right',
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
      
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      // Even if there's an error, we still want to clear the auth state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      return { success: false };
    }
  };

  // Debug: Log toast container status
  // useEffect(() => {
  //   console.log('Toast container status:', {
  //     isToastContainerMounted: document.querySelector('.Toastify') !== null,
  //     toast: typeof toast,
  //     toastContainer: document.querySelector('.Toastify')
  //   });
  // }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Export the provider as a named export
export { AuthProvider };

// Export the hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthProvider;