import api from "./api";
import type { CurrentUser } from "./authTypes";

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUser>("/accounts/me/");
  return response.data;
}
