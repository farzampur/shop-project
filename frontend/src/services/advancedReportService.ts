import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export type ReportFilter = {
  store?: number;
  start_date?: string;
  end_date?: string;
};

const params = (filter: ReportFilter = {}) => ({
  params: Object.fromEntries(
    Object.entries(filter).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ),
});

const list = <T,>(data: ApiListResponse<T>): T[] => (Array.isArray(data) ? data : data.results);

export async function inventoryLowStock(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/inventory-low-stock/", params(filter))).data);
}
export async function inventoryOutOfStock(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/inventory-out-of-stock/", params(filter))).data);
}
export async function inventoryValueReport(filter?: ReportFilter) {
  return (await api.get<unknown>("/products/inventory-value-report/", params(filter))).data;
}
export async function inventorySlowMoving(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/inventory-slow-moving/", params(filter))).data);
}
export async function inventoryPotentialProfit(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/inventory-potential-profit/", params(filter))).data);
}
export async function storeInventorySummary(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/store-inventory-summary/", params(filter))).data);
}
export async function fullInventoryReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/inventory-report-full/", params(filter))).data);
}
export async function inventoryDashboard(filter?: ReportFilter) {
  return (await api.get<unknown>("/products/inventory-dashboard/", params(filter))).data;
}

export async function supplierDebtors(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/suppliers/debtors/", params(filter))).data);
}
export async function supplierPurchaseReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/suppliers/purchase-report/", params(filter))).data);
}
export async function supplierPaymentReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/suppliers/payment-report/", params(filter))).data);
}
export async function supplierBalanceReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/suppliers/balance-report/", params(filter))).data);
}
export async function supplierComprehensiveReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/products/suppliers/comprehensive-report/", params(filter))).data);
}

export async function customerReport(filter?: ReportFilter) {
  return (await api.get<unknown>("/sales/customer-report/", params(filter))).data;
}
export async function customerDebtors(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/sales/customers/debtors/", params(filter))).data);
}
export async function customerCreditors(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/sales/customers/creditors/", params(filter))).data);
}

export async function financialSummary(filter?: ReportFilter) {
  return (await api.get<unknown>("/sales/financial-summary/", params(filter))).data;
}
export async function financialReport(filter?: ReportFilter) {
  return (await api.get<unknown>("/sales/financial-report/", params(filter))).data;
}
export async function cashLedger(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/sales/cash-ledger/", params(filter))).data);
}
export async function cashboxBalanceReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/sales/cashbox-balance-report/", params(filter))).data);
}
export async function dailyCashFlowReport(filter?: ReportFilter) {
  return list((await api.get<ApiListResponse<unknown>>("/sales/daily-cash-flow-report/", params(filter))).data);
}
