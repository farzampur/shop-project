import axios from "axios";
import { tokenService } from "./tokenService";
import { getApiErrorMessage } from "../utils/apiError";

const AUTH_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

const authApi = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
  timeout: 15000,

  // Django CSRF defaults
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",

  // Required when frontend/API are different origins in development.
  withXSRFToken: true,
});

authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    error.message = getApiErrorMessage(error, "ارتباط با سرور با خطا مواجه شد.");
    return Promise.reject(error);
  },
);

export interface LoginResponse {
  access: string;
}

export interface RefreshResponse {
  access: string;
}

let csrfReady = false;
let csrfPromise: Promise<void> | null = null;
let refreshPromise: Promise<string> | null = null;

async function ensureCsrfCookie(): Promise<void> {
  if (csrfReady) {
    return;
  }

  if (!csrfPromise) {
    csrfPromise = authApi
      .get("/auth/csrf/")
      .then(() => {
        csrfReady = true;
      })
      .finally(() => {
        csrfPromise = null;
      });
  }

  await csrfPromise;
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await authApi.post<LoginResponse>(
    "/auth/token/",
    {
      username,
      password,
    }
  );

  return response.data;
}

export function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      await ensureCsrfCookie();

      const response = await authApi.post<RefreshResponse>(
        "/auth/token/refresh/",
        {}
      );

      const newAccessToken = response.data.access;

      tokenService.saveAccessToken(newAccessToken);

      return newAccessToken;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

export function saveTokens(tokens: LoginResponse) {
  tokenService.saveAccessToken(tokens.access);
}

export async function logout(): Promise<void> {
  // Access token را فوراً محلی پاک می‌کنیم، اما قبل از بستن صفحه اجازه می‌دهیم
  // درخواست blacklist فرصت کامل شدن داشته باشد تا مرورگر اتصال Django را قطع نکند.
  tokenService.clearTokens();
  window.dispatchEvent(new Event("auth-change"));

  try {
    csrfReady = false;
    await Promise.race([
      (async () => {
        await ensureCsrfCookie();
        await authApi.post("/auth/token/blacklist/", {});
      })(),
      new Promise<void>((resolve) => window.setTimeout(resolve, 3000)),
    ]);
  } catch (error) {
    // خروج محلی انجام شده؛ خطای blacklist نباید مانع خروج شود.
    console.warn("LOGOUT BLACKLIST FAILED:", error);
  }
}
