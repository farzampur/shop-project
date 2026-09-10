import api from "./api";
import type { StoreRole } from "./authTypes";

export interface ManagedUser {
  id: number;
  user: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  store: number;
  store_name: string;
  role: StoreRole;
  role_display: string;
  is_active: boolean;
  created_at: string;
}

export interface CreateManagedUserPayload {
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  role: StoreRole;
  store: number;
}

export async function listManagedUsers(storeId: number): Promise<ManagedUser[]> {
  const response = await api.get<ManagedUser[]>(`/accounts/store-users/?store=${storeId}`);
  return Array.isArray(response.data) ? response.data : (response.data as any)?.results ?? [];
}

export async function createManagedUser(payload: CreateManagedUserPayload) {
  const response = await api.post<ManagedUser>("/accounts/store-users/", payload);
  return response.data;
}

export async function updateManagedUser(id: number, payload: Partial<Pick<ManagedUser, "role" | "is_active">>) {
  const response = await api.patch<ManagedUser>(`/accounts/store-users/${id}/`, payload);
  return response.data;
}

export async function deleteManagedUser(id: number) {
  await api.delete(`/accounts/store-users/${id}/`);
}
