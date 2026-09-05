import api from "./api";
import type { ApiListResponse } from "./apiTypes";
import type { Product } from "./productService";

export interface Supplier {
  id: number;
  name: string;
}

export interface PurchaseItem {
  id: number;
  product: number;
  product_name: string;
  quantity: string;
  unit_price: string;
  total_price: string;
}

export interface Purchase {
  id: number;
  supplier: number;
  supplier_name: string;
  store: number;
  store_name: string;
  user?: number;
  invoice_number: string;
  total_amount: string;
  created_at: string;
  received: boolean;
  username: string;
  item_count: number;
  items: PurchaseItem[];
}

export interface PurchaseItemInput {
  product: number;
  quantity: string;
  unit_price: string;
}

export interface PurchaseWriteData {
  supplier: number;
  store: number;
  invoice_number: string;
  received: boolean;
  items: PurchaseItemInput[];
}

export interface PurchaseReturnData {
  purchase: number;
  product: number;
  quantity: string;
  unit_price: string;
}

export async function listPurchases(storeId: number): Promise<Purchase[]> {
  const response = await api.get<ApiListResponse<Purchase>>("/products/purchases/", {
    params: { store: storeId },
  });
  return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function listSuppliers(storeId: number): Promise<Supplier[]> {
  const response = await api.get<ApiListResponse<Supplier>>("/products/suppliers/", {
    params: { store: storeId },
  });
  return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function listPurchaseProducts(storeId: number): Promise<Product[]> {
  const response = await api.get<ApiListResponse<Product>>("/products/products/", {
    params: { store: storeId },
  });
  return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function createPurchase(data: PurchaseWriteData): Promise<Purchase> {
  const response = await api.post<Purchase>("/products/purchases/", data);
  return response.data;
}

export async function updatePurchase(id: number, data: PurchaseWriteData): Promise<Purchase> {
  const response = await api.put<Purchase>(`/products/purchases/${id}/`, data);
  return response.data;
}

export async function deletePurchase(id: number): Promise<void> {
  await api.delete(`/products/purchases/${id}/`);
}

export async function receivePurchase(id: number): Promise<Purchase> {
  const response = await api.post<Purchase>(`/products/purchases/${id}/receive/`);
  return response.data;
}

export async function createPurchaseReturn(data: PurchaseReturnData): Promise<void> {
  await api.post("/products/purchase-returns/", data);
}
