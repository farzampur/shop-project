import axios from "axios";
import type {
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

import { refreshAccessToken, logout } from "./authService";
import { tokenService } from "./tokenService";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});



function isAuthEndpoint(url = "") {
  return (
    url.includes("/auth/token/") ||
    url.includes("/auth/token/refresh/")
  );
}


api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (isAuthEndpoint(config.url)) {
      return config;
    }

    const accessToken = tokenService.getAccessToken();

    if (accessToken) {
      config.headers.set(
        "Authorization",
        `Bearer ${accessToken}`
      );
    }

    return config;
  }
);

api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & {
          _retry?: boolean;
        })
      | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isAuthEndpoint(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const newAccessToken = await refreshAccessToken();

      originalRequest.headers.set(
        "Authorization",
        `Bearer ${newAccessToken}`
      );

      return api(originalRequest);
    } catch (refreshError) {
      void logout();

      return Promise.reject(refreshError);
    }
  }
);

export default api;