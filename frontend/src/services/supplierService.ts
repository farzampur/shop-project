import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface Supplier {
  id: number;
  store: number;
  store_name?: string;
  name: string;
  phone: string;
  address: string;
  description: string;
  created_at?: string;
  updated_at?: string;
}

export interface SupplierTx {
  id: number;
  supplier: number;
  transaction_type: string;
  amount: string | number;
  reference_id: number | null;
  description: string;
  created_at: string;
}

export interface SupplierBalance {
  supplier_id: number;
  supplier_name: string;
  purchases: string | number;
  payments: string | number;
  returns: string | number;
  balance: string | number;
}

export interface SupplierSettlement {
  supplier_id: number;
  supplier_name: string;
  settled_amount: string | number;
  remaining_balance: string | number;
  cashbox_id: number;
  cashbox_name: string;
}

const list = <T,>(d: ApiListResponse<T>) => Array.isArray(d) ? d : d.results;

export async function listSuppliers(storeId: number) {
  const r = await api.get<ApiListResponse<Supplier>>("/products/suppliers/", { params: { store: storeId } });
  return list(r.data);
}

export async function createSupplier(data: Partial<Supplier> & { store: number }) {
  return (await api.post<Supplier>("/products/suppliers/", data)).data;
}

export async function updateSupplier(id: number, data: Partial<Supplier>) {
  return (await api.patch<Supplier>(`/products/suppliers/${id}/`, data)).data;
}

export async function deleteSupplier(id: number) {
  await api.delete(`/products/suppliers/${id}/`);
}

export async function supplierBalance(id: number) {
  return (await api.get<SupplierBalance>(`/products/suppliers/${id}/balance/`)).data;
}

export async function supplierLedger(id: number) {
  return (await api.get<ApiListResponse<SupplierTx>>(`/products/suppliers/${id}/ledger/`)).data;
}

export async function paySupplier(data: { supplier: number; amount: number; cashbox: number; description?: string }) {
  return (await api.post("/products/supplier-payments/", data)).data;
}

export async function settleSupplier(supplierId: number, cashbox: number) {
  return (await api.post<SupplierSettlement>(`/products/suppliers/${supplierId}/settle/`, { cashbox })).data;
}
