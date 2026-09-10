import api from "./api";

export interface ManagedStore {
  id: number;
  name: string;
  code: string;
  phone: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  manager_username: string | null;
}

export interface StorePayload {
  name: string;
  code: string;
  phone?: string;
  address?: string;
  is_active?: boolean;
}

export async function listStores() {
  const response = await api.get<ManagedStore[]>("/stores/");
  return Array.isArray(response.data) ? response.data : (response.data as any)?.results ?? [];
}

export async function createStore(payload: StorePayload) {
  const response = await api.post<ManagedStore>("/stores/", payload);
  return response.data;
}

export async function updateStore(id: number, payload: Partial<StorePayload>) {
  const response = await api.patch<ManagedStore>(`/stores/${id}/`, payload);
  return response.data;
}

export async function deleteStore(id: number) {
  await api.delete(`/stores/${id}/`);
}
