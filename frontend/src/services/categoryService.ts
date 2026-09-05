import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface Category {
  id: number;
  name: string;
  store: number;
  store_name?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface CreateCategoryData {
  name: string;
  store: number;
}

export async function listCategories(storeId: number): Promise<Category[]> {
  const response = await api.get<ApiListResponse<Category>>("/products/categories/", {
    params: { store: storeId },
  });
  return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function createCategory(data: CreateCategoryData): Promise<Category> {
  const response = await api.post<Category>("/products/categories/", data);
  return response.data;
}

export async function deleteCategory(id: number, storeId: number): Promise<void> {
  await api.delete(`/products/categories/${id}/`, {
    params: { store: storeId },
  });
}
