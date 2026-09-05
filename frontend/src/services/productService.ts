import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface Product {
  id: number;
  name: string;
  barcode?: string;
  category: number;
  category_name?: string;
  unit?: string;
  purchase_price?: string;
  sale_price?: string;
  is_active?: boolean;
}

export interface ProductWriteData {
  name: string;
  category: number;
  unit: string;
  purchase_price: string;
  sale_price: string;
  is_active: boolean;
  barcode?: string;
}

export async function listProducts(storeId: number): Promise<Product[]> {
  const response = await api.get<ApiListResponse<Product>>("/products/products/", {
    params: { store: storeId },
  });
  return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function createProduct(storeId: number, data: ProductWriteData): Promise<Product> {
  const response = await api.post<Product>("/products/products/", data, {
    params: { store: storeId },
  });
  return response.data;
}

export async function updateProduct(
  id: number,
  storeId: number,
  data: ProductWriteData,
): Promise<Product> {
  const response = await api.patch<Product>(`/products/products/${id}/`, data, {
    params: { store: storeId },
  });
  return response.data;
}

export async function deleteProduct(id: number): Promise<void> {
  await api.delete(`/products/products/${id}/`);
}
