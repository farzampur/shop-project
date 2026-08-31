import api from "./api";
import { tokenService } from "./tokenService";

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
  const response = await api.post<LoginResponse>(
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

  const response = await api.post<RefreshResponse>(
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
  window.dispatchEvent(
    new Event("auth-change")
  );
}