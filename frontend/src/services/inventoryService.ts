import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface InventoryItem {
  id: number;
  product: number;
  product_name: string;
  barcode?: string;
  store: number;
  store_name: string;
  quantity: string;
  min_quantity: string;
  updated_at?: string;
}

export interface InventoryTransaction {
  id: number;
  transaction_type: string;
  quantity: string;
  reference_id?: number | null;
  description?: string;
  created_at?: string;
}

function unwrapList<T>(data: ApiListResponse<T>): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listInventory(storeId: number): Promise<InventoryItem[]> {
  const response = await api.get<ApiListResponse<InventoryItem>>("/products/inventory/", {
    params: { store: storeId },
  });
  return unwrapList(response.data);
}

export async function listInventoryTransactions(
  storeId: number,
  productId?: number,
): Promise<InventoryTransaction[]> {
  const response = await api.get<ApiListResponse<InventoryTransaction>>(
    "/products/transactions/",
    {
      params: {
        store: storeId,
        ...(productId ? { product: productId } : {}),
      },
    },
  );
  return unwrapList(response.data);
}

export async function updateInventoryMinimum(
  id: number,
  storeId: number,
  minQuantity: string,
): Promise<InventoryItem> {
  const response = await api.patch<InventoryItem>(
    `/products/inventory/${id}/`,
    { min_quantity: minQuantity },
    { params: { store: storeId } },
  );
  return response.data;
}
