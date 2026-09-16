import axios from "axios";
import { tokenService } from "./tokenService";

const AUTH_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

const authApi = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,

  // Django CSRF defaults
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",

  // Required when frontend/API are different origins in development.
  withXSRFToken: true,
});

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

export async function logout() {
  try {
    await ensureCsrfCookie();

    await authApi.post(
      "/auth/token/blacklist/",
      {}
    );
  } finally {
    tokenService.clearTokens();
    window.dispatchEvent(new Event("auth-change"));
  }
}