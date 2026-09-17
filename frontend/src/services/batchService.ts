import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface ProductBatch {
  id: number;
  product: number;
  product_name: string;
  barcode?: string | null;
  store: number;
  store_name: string;
  quantity: string;
  remaining_quantity: string;
  purchase_price: string;
  sale_price: string;
  received_at: string;
  source_batch?: number | null;
}

function unwrap<T>(data: ApiListResponse<T>): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listProductBatches(
  storeId: number,
  options?: { productId?: number; remaining?: "active" | "empty" },
): Promise<ProductBatch[]> {
  const response = await api.get<ApiListResponse<ProductBatch>>("/products/batches/", {
    params: {
      store: storeId,
      ...(options?.productId ? { product: options.productId } : {}),
      ...(options?.remaining ? { remaining: options.remaining } : {}),
    },
  });
  return unwrap(response.data);
}
