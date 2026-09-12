import api from "./api";

export type ReportParams = { store?: number | null; start_date?: string; end_date?: string };
const query = (p: ReportParams = {}) => ({ params: Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined && v !== null && v !== "")) });
export type Daily = { day: string; order_count: number; total_sales: string };
export type Monthly = { month: string; order_count: number; total_sales: string };
export type PaymentMethod = { method: string; method_name: string; amount: string; transaction_count: number };
export type TopProduct = { product_id: number; product_name: string; total_quantity: string; total_sales: string };
export type Profit = { total_sales: string; total_cost: string; total_profit: string };
export type Financial = { sales: string; expenses: string; balance: string };
export type Cancellation = { order_id: number; store: string; cancelled_by: string | null; cancelled_at: string; reason: string; amount: string };
export type CashRecon = { id: number; name: string; store: string; balance: string; ledger_balance: string; difference: string; is_balanced: boolean };
export type Summary = { order_count:number; sales:string; before_discount:string; discount:string; cost:string; gross_profit:string; cancelled_count:number; cancelled_sales:string; cash:string; card:string; credit:string };

export async function summaryReport(p?: ReportParams) { return (await api.get<Summary>("/sales/sales-report/summary/", query(p))).data; }
export async function dailySales(p?: ReportParams) { return (await api.get<Daily[]>("/sales/sales-report/", query(p))).data; }
export async function monthlySales(p?: ReportParams) { return (await api.get<Monthly[]>("/sales/sales-report/monthly/", query(p))).data; }
export async function paymentMethods(p?: ReportParams) { return (await api.get<PaymentMethod[]>("/sales/sales-report/payment_methods/", query(p))).data; }
export async function topProducts(p?: ReportParams) { return (await api.get<TopProduct[]>("/sales/sales-report/top_products/", query(p))).data; }
export async function profitReport(p?: ReportParams) { return (await api.get<Profit>("/sales/sales-report/profit/", query(p))).data; }
export async function financialReport(p?: ReportParams) { return (await api.get<Financial>("/sales/sales-report/financial/", query(p))).data; }
export async function cancellationsReport(p?: ReportParams) { return (await api.get<Cancellation[]>("/sales/sales-report/cancellations/", query(p))).data; }
export async function cashReconciliation(p?: ReportParams) { return (await api.get<CashRecon[]>("/sales/sales-report/cash-reconciliation/", query(p))).data; }

export type StoreComparison = { store_id:number; store__name:string; order_count:number; total_sales:string; total_discount:string; cost:string; gross_profit:string };
export type SellerPerformance = { user_id:number; user__username:string; store_id:number; store__name:string; order_count:number; total_sales:string };
export type InventoryOverview = { store_id:number; store_name:string; quantity:string; inventory_value:string; low_stock_count:number; product_count:number };
export type LowStock = { store_id:number; store_name:string; product_id:number; product_name:string; quantity:string; min_quantity:string };
export async function storeComparison(p?: ReportParams) { return (await api.get<StoreComparison[]>("/sales/sales-report/store_comparison/", query(p))).data; }
export async function sellerPerformance(p?: ReportParams) { return (await api.get<SellerPerformance[]>("/sales/sales-report/seller_performance/", query(p))).data; }
export async function inventoryOverview(p?: ReportParams) { return (await api.get<InventoryOverview[]>("/sales/sales-report/inventory_overview/", query(p))).data; }
export async function lowStockReport(p?: ReportParams) { return (await api.get<LowStock[]>("/sales/sales-report/low_stock/", query(p))).data; }
