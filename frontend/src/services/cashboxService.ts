import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface CashBox {
  id: number;
  name: string;
  store: number;
  balance: string | number;
  description?: string;
  created_at?: string;
}

export interface CashBoxTransaction {
  id: number;
  cashbox: number;
  transaction_type: "deposit" | "withdraw" | "receive" | "payment";
  amount: string | number;
  description: string;
  reference_id: number | null;
  created_at: string;
}

export async function listCashBoxes(storeId: number): Promise<CashBox[]> {
  const r = await api.get<ApiListResponse<CashBox>>("/sales/cashboxes/", { params: { store: storeId } });
  return Array.isArray(r.data) ? r.data : r.data.results;
}

export async function createCashBox(data: { name: string; store: number; description?: string }): Promise<CashBox> {
  return (await api.post<CashBox>("/sales/cashboxes/", data)).data;
}

export async function updateCashBox(id: number, data: { name?: string; description?: string }): Promise<CashBox> {
  return (await api.patch<CashBox>(`/sales/cashboxes/${id}/`, data)).data;
}

export async function deleteCashBox(id: number): Promise<void> {
  await api.delete(`/sales/cashboxes/${id}/`);
}

export async function listCashBoxTransactions(storeId: number): Promise<CashBoxTransaction[]> {
  const r = await api.get<ApiListResponse<CashBoxTransaction>>("/sales/cashbox-transactions/", { params: { store: storeId } });
  return Array.isArray(r.data) ? r.data : r.data.results;
}

export async function createCashBoxTransaction(data: {
  cashbox: number;
  transaction_type: "deposit" | "withdraw";
  amount: number;
  description?: string;
}): Promise<CashBoxTransaction> {
  return (await api.post<CashBoxTransaction>("/sales/cashbox-transactions/", data)).data;
}

export interface CashTransfer { id:number; from_cashbox:number; to_cashbox:number; amount:string|number; description:string; created_by:number; created_at:string }
export async function listCashTransfers(storeId:number){ const r=await api.get<ApiListResponse<CashTransfer>>("/sales/cash-transfers/",{params:{store:storeId}}); return Array.isArray(r.data)?r.data:r.data.results; }
export async function createCashTransfer(data:{from_cashbox:number;to_cashbox:number;amount:number;description?:string}){ return (await api.post<CashTransfer>("/sales/cash-transfers/",data)).data; }
export interface Expense { id:number; store:number; cashbox:number; expense_type:string; title:string; amount:string|number; description:string; expense_date:string; created_at:string }
export async function listExpenses(storeId:number){ const r=await api.get<ApiListResponse<Expense>>("/sales/expenses/",{params:{store:storeId}}); return Array.isArray(r.data)?r.data:r.data.results; }
export async function createExpense(data:Omit<Expense,"id"|"created_at">){ return (await api.post<Expense>("/sales/expenses/",data)).data; }
