import api from "./api";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await api.post<AuthResponse>(
      "/api/v1/auth/login",
      formData,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    // Store tokens
    localStorage.setItem("access_token", response.data.access_token);
    if (response.data.refresh_token) {
      localStorage.setItem("refresh_token", response.data.refresh_token);
    }

    return response.data;
  },

  async logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem("access_token");
  },

  getAccessToken(): string | null {
    return localStorage.getItem("access_token");
  },

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await api.post<AuthResponse>("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });

    // Update stored tokens
    localStorage.setItem("access_token", response.data.access_token);
    if (response.data.refresh_token) {
      localStorage.setItem("refresh_token", response.data.refresh_token);
    }

    return response.data.access_token;
  },
};

export default authService;
