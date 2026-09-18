import api from "./api";

export type ReportFilter = { store?: number | null; start_date?: string; end_date?: string };

const query = (filter: ReportFilter = {}) => ({
  params: Object.fromEntries(
    Object.entries(filter).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ),
});

const get = async <T = unknown>(path: string, filter?: ReportFilter): Promise<T> =>
  (await api.get<T>(path, query(filter))).data;

export const inventoryLowStock = (f?: ReportFilter) => get("/products/inventory-low-stock/", f);
export const inventoryOutOfStock = (f?: ReportFilter) => get("/products/inventory-out-of-stock/", f);
export const inventoryValueReport = (f?: ReportFilter) => get("/products/inventory-value-report/", f);
export const inventorySlowMoving = (f?: ReportFilter) => get("/products/inventory-slow-moving/", f);
export const inventoryPotentialProfit = (f?: ReportFilter) => get("/products/inventory-potential-profit/", f);
export const storeInventorySummary = (f?: ReportFilter) => get("/products/store-inventory-summary/", f);
export const fullInventoryReport = (f?: ReportFilter) => get("/products/inventory-report-full/", f);
export const inventoryDashboard = (f?: ReportFilter) => get("/products/inventory-dashboard/", f);

export const supplierDebtors = (f?: ReportFilter) => get("/products/suppliers/debtors/", f);
export const supplierPurchaseReport = (f?: ReportFilter) => get("/products/suppliers/purchase-report/", f);
export const supplierPaymentReport = (f?: ReportFilter) => get("/products/suppliers/payment-report/", f);
export const supplierBalanceReport = (f?: ReportFilter) => get("/products/suppliers/balance-report/", f);
export const supplierComprehensiveReport = (f?: ReportFilter) => get("/products/suppliers/comprehensive-report/", f);

export const customerReport = (f?: ReportFilter) => get("/sales/customer-report/", f);
export const customerDebtors = (f?: ReportFilter) => get("/sales/customers/debtors/", f);
export const customerCreditors = (f?: ReportFilter) => get("/sales/customers/creditors/", f);

export const financialSummary = (f?: ReportFilter) => get("/sales/financial-summary/", f);
export const financialReport = (f?: ReportFilter) => get("/sales/financial-report/", f);
export const cashLedger = (f?: ReportFilter) => get("/sales/cash-ledger/", f);
export const cashboxBalanceReport = (f?: ReportFilter) => get("/sales/cashbox-balance-report/", f);
export const dailyCashFlowReport = (f?: ReportFilter) => get("/sales/daily-cash-flow-report/", f);
