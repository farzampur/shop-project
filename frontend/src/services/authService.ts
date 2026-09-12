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
});

export interface LoginResponse {
  access: string;
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
  const response = await authApi.post<RefreshResponse>(
    "/auth/token/refresh/",
    {}
  );

  const newAccessToken = response.data.access;

  tokenService.saveAccessToken(newAccessToken);

  return newAccessToken;
}

export function saveTokens(tokens: LoginResponse) {
  tokenService.saveAccessToken(tokens.access);
}

export async function logout() {
  try {
    await authApi.post("/auth/token/blacklist/", {});
  } finally {
    tokenService.clearTokens();
    window.dispatchEvent(new Event("auth-change"));
  }
}