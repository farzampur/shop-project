import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import { refreshAccessToken, logout } from "./authService";
import { tokenService } from "./tokenService";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: { "Content-Type": "application/json" },
});

let refreshPromise: Promise<string> | null = null;

function isAuthEndpoint(url = "") {
  return url.includes("/auth/token/") || url.includes("/auth/token/refresh/");
}

async function refreshOnce(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Authentication endpoints must not receive an old/expired bearer token.
  if (isAuthEndpoint(config.url)) return config;

  const accessToken = tokenService.getAccessToken();
  if (accessToken) {
    // Axios 1.x uses AxiosHeaders internally; assigning through set() avoids
    // silently losing the header when a plain object is supplied by a caller.
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isAuthEndpoint(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    const refreshToken = tokenService.getRefreshToken();
    if (!refreshToken) return Promise.reject(error);

    originalRequest._retry = true;

    try {
      const newAccessToken = await refreshOnce();
      originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
      return api(originalRequest);
    } catch (refreshError) {
      logout();
      return Promise.reject(refreshError);
    }
  }
);

export default api;
