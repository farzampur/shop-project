import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface Customer {
  id: number;
  store: number;
  first_name: string;
  last_name: string;
  mobile: string;
  address: string;
  created_at?: string;
}

export interface CustomerBalance {
  customer_id: number;
  customer_name: string;
  sales: string | number;
  payments: string | number;
  balance: string | number;
}

export interface CustomerLedgerItem {
  id: number;
  date: string;
  type: "sale" | "payment";
  amount: string | number;
  description: string;
  balance: string | number;
}

export interface CustomerLedger {
  customer_id: number;
  customer_name: string;
  transactions: CustomerLedgerItem[];
  final_balance: string | number;
}

export interface CustomerTransaction {
  id: number;
  customer: number;
  store: number;
  transaction_type: "sale" | "payment";
  amount: string | number;
  description: string;
  reference_id: number | null;
  created_at: string;
}

export async function listCustomers(storeId: number): Promise<Customer[]> {
  const r = await api.get<ApiListResponse<Customer>>("/sales/customers/", { params: { store: storeId } });
  return Array.isArray(r.data) ? r.data : r.data.results;
}

export async function createCustomer(data: Omit<Customer, "id">): Promise<Customer> {
  return (await api.post<Customer>("/sales/customers/", data)).data;
}

export async function updateCustomer(id: number, data: Partial<Omit<Customer, "id" | "store">>): Promise<Customer> {
  return (await api.patch<Customer>(`/sales/customers/${id}/`, data)).data;
}

export async function deleteCustomer(id: number): Promise<void> {
  await api.delete(`/sales/customers/${id}/`);
}

export async function getCustomerBalance(customerId: number): Promise<CustomerBalance> {
  return (await api.get<CustomerBalance>(`/sales/customers/${customerId}/balance/`)).data;
}

export async function getCustomerLedger(customerId: number): Promise<CustomerLedger> {
  return (await api.get<CustomerLedger>(`/sales/customers/${customerId}/ledger/`)).data;
}

export async function listCustomerTransactions(storeId: number): Promise<CustomerTransaction[]> {
  const r = await api.get<ApiListResponse<CustomerTransaction>>("/sales/customer-transactions/", { params: { store: storeId } });
  return Array.isArray(r.data) ? r.data : r.data.results;
}

export async function createCustomerPayment(data: {
  customer: number;
  transaction_type: "payment";
  amount: number;
  description?: string;
  cashbox: number;
}): Promise<CustomerTransaction> {
  return (await api.post<CustomerTransaction>("/sales/customer-transactions/", data)).data;
}
