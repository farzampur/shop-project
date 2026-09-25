import axios from "axios";
import type {
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

import { refreshAccessToken, logout } from "./authService";
import { tokenService } from "./tokenService";
import { getApiErrorMessage } from "../utils/apiError";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
  timeout: 15000,
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

    // Every store-scoped request carries the active store explicitly.
    // The backend still validates ownership; this is only a client-side
    // consistency guard that prevents stale data from another store when
    // switching branches.
    const url = config.url || "";
    const isGlobalEndpoint =
      url.startsWith("/stores") ||
      url.startsWith("/accounts/me") ||
      url.startsWith("/auth/");
    if (!isGlobalEndpoint) {
      const activeStoreId = Number(localStorage.getItem("active_store_id"));
      if (Number.isInteger(activeStoreId) && activeStoreId > 0) {
        const params = config.params instanceof URLSearchParams
          ? config.params
          : { ...(config.params ?? {}) };
        if (params instanceof URLSearchParams) {
          if (!params.has("store")) params.set("store", String(activeStoreId));
        } else if (params.store === undefined || params.store === null || params.store === "") {
          params.store = activeStoreId;
        }
        config.params = params;
      }
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
    error.message = getApiErrorMessage(error, "ارتباط با سرور با خطا مواجه شد.");

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