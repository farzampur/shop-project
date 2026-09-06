import axios from "axios";
import { tokenService } from "./tokenService";

const AUTH_BASE_URL = "http://127.0.0.1:8000/api";

const authApi = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface RefreshResponse {
  access: string;
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

export async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenService.getRefreshToken();

  if (!refreshToken) {
    throw new Error("Refresh token not found");
  }

  const response = await authApi.post<RefreshResponse>(
    "/auth/token/refresh/",
    {
      refresh: refreshToken,
    }
  );

  const newAccessToken = response.data.access;
  tokenService.saveAccessToken(newAccessToken);

  return newAccessToken;
}

export function saveTokens(tokens: LoginResponse) {
  tokenService.saveTokens(tokens.access, tokens.refresh);
}

export function logout() {
  tokenService.clearTokens();
  window.dispatchEvent(new Event("auth-change"));
}
