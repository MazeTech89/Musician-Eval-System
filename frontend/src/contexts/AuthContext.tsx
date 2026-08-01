import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import api, { clearStoredAuthTokens, setStoredAuthTokens } from "../api/axios";
import { getApiErrorMessage } from "../utils/form";

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  email_verified?: boolean;
  mfa_enabled?: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string, totpCode?: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const response = await api.get("/auth/me");
        setUser(response.data);
      } catch (error) {
        clearStoredAuthTokens();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (username: string, password: string, totpCode?: string) => {
    try {
      const response = await api.post("/auth/login", {
        username,
        password,
        totp_code: totpCode || undefined,
      });
      const { access_token, refresh_token } = response.data ?? {};
      setStoredAuthTokens(access_token, refresh_token);

      const profileResponse = await api.get("/auth/me");
      setUser(profileResponse.data);
    } catch (error) {
      clearStoredAuthTokens();
      throw new Error(getApiErrorMessage(error, "Login failed"));
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      await api.post("/auth/register", userData);
    } catch (error) {
      throw new Error(getApiErrorMessage(error, "Registration failed"));
    }
  };

  const logout = () => {
    clearStoredAuthTokens();
    api.post("/auth/logout").catch(() => undefined);
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
