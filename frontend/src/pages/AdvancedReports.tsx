import { useEffect, useMemo, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Divider,
  Stack, Tab, Tabs, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import JalaliDateInput from "../components/JalaliDateInput";
import { jalaliDateToIsoDate, todayJalali, toJalali, formatJalali, formatJalaliDate, formatJalaliDateTime } from "../utils/jalaliDate";
import InventoryIcon from "@mui/icons-material/Inventory";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import PeopleIcon from "@mui/icons-material/People";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import { useStore } from "../contexts/StoreContext";
import {
  inventoryLowStock, inventoryOutOfStock, inventoryValueReport, inventorySlowMoving,
  inventoryPotentialProfit, storeInventorySummary, fullInventoryReport, inventoryDashboard,
  supplierDebtors, supplierPurchaseReport, supplierPaymentReport, supplierBalanceReport,
  supplierComprehensiveReport, customerReport, customerDebtors, customerCreditors,
  financialSummary, financialReport, cashLedger, cashboxBalanceReport, dailyCashFlowReport,
  type ReportFilter,
} from "../services/advancedReportService";

const errorMessage = (e: any) => e?.response?.data?.detail || e?.response?.data?.message || "دریافت گزارش انجام نشد.";

function normalizeRows(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) return data.filter((x): x is Record<string, unknown> => !!x && typeof x === "object");
  if (data && typeof data === "object") return [data as Record<string, unknown>];
  return [];
}

function label(key: string) {
  const labels: Record<string, string> = {
    id: "شناسه",
    product_id: "شناسه کالا",
    product_name: "کالا",
    store_id: "شناسه فروشگاه",
    store_name: "فروشگاه",
    supplier_id: "شناسه تأمین‌کننده",
    supplier_name: "تأمین‌کننده",
    customer_id: "شناسه مشتری",
    customer_name: "مشتری",
    cashbox_id: "شناسه صندوق",
    cashbox_name: "صندوق",
    inventory_id: "شناسه موجودی",
    batch_id: "شناسه بچ",
    quantity: "مقدار",
    remaining_quantity: "مانده مقدار",
    min_quantity: "حداقل موجودی",
    max_quantity: "حداکثر موجودی",
    inventory_quantity: "موجودی",
    inventory_value: "ارزش موجودی",
    potential_profit: "سود بالقوه",
    total_potential_profit: "سود بالقوه کل",
    purchase_price: "قیمت خرید",
    sale_price: "قیمت فروش",
    average_purchase_price: "میانگین قیمت خرید",
    total: "جمع",
    count: "تعداد",
    amount: "مبلغ",
    total_amount: "مبلغ کل",
    balance: "مانده",
    status: "وضعیت",
    total_sales: "مجموع فروش",
    total_sale: "مجموع فروش",
    sales_amount: "مبلغ فروش",
    total_cost: "مجموع هزینه",
    total_profit: "مجموع سود",
    profit: "سود",
    gross_profit: "سود ناخالص",
    net_profit: "سود خالص",
    discount: "تخفیف",
    discount_amount: "مبلغ تخفیف",
    total_discount: "مجموع تخفیف",
    total_discount_amount: "مجموع مبلغ تخفیف",
    purchase_count: "تعداد خرید",
    total_purchase: "مجموع خرید",
    average_purchase: "میانگین خرید",
    last_purchase: "آخرین خرید",
    last_purchase_date: "تاریخ آخرین خرید",
    first_purchase: "اولین خرید",
    first_purchase_date: "تاریخ اولین خرید",
    payment_count: "تعداد پرداخت",
    total_payment: "مجموع پرداخت",
    payment_total: "مجموع پرداخت",
    payments: "پرداخت‌ها",
    payment_amount: "مبلغ پرداخت",
    average_payment: "میانگین پرداخت",
    last_payment: "آخرین پرداخت",
    last_payment_date: "تاریخ آخرین پرداخت",
    return_count: "تعداد برگشت",
    total_return: "مجموع برگشت",
    returns: "برگشت‌ها",
    adjustment_count: "تعداد تعدیلات",
    adjustment: "تعدیل",
    adjustments: "تعدیلات",
    adjustment_total: "مجموع تعدیلات",
    transaction_count: "تعداد تراکنش",
    transaction_type: "نوع تراکنش",
    transaction: "تراکنش",
    payment_method: "روش پرداخت",
    payment_methods: "روش‌های پرداخت",
    method: "روش",
    receipts: "دریافت‌ها",
    receipt_count: "تعداد دریافت",
    receipt_total: "مجموع دریافت",
    expenses: "هزینه‌ها",
    expense_amount: "مبلغ هزینه",
    expense_count: "تعداد هزینه",
    purchase_returns: "برگشت خرید",
    sale_returns: "برگشت فروش",
    order_count: "تعداد سفارش",
    sales_count: "تعداد فروش",
    customer_count: "تعداد مشتری",
    supplier_count: "تعداد تأمین‌کننده",
    debtor_count: "تعداد بدهکار",
    creditor_count: "تعداد بستانکار",
    debt: "بدهی",
    credit: "بستانکاری",
    payable: "بدهی قابل پرداخت",
    receivable: "مطالبات قابل دریافت",
    total_debt: "مجموع بدهی",
    total_credit: "مجموع بستانکاری",
    total_receivable: "مجموع مطالبات",
    total_payable: "مجموع بدهی قابل پرداخت",
    cash_balance: "مانده نقدی",
    cashbox_balance: "مانده صندوق",
    opening_balance: "موجودی ابتدای دوره",
    closing_balance: "موجودی پایان دوره",
    debit: "بدهکار",
    credit_amount: "مبلغ بستانکاری",
    description: "توضیحات",
    invoice_number: "شماره فاکتور",
    order_id: "شناسه سفارش",
    purchase_id: "شناسه خرید",
    payment_id: "شناسه پرداخت",
    reference_id: "شناسه مرجع",
    created_at: "تاریخ ایجاد",
    updated_at: "تاریخ آخرین تغییر",
    date: "تاریخ",
    day: "روز",
    month: "ماه",
    year: "سال",
    start_date: "از تاریخ",
    end_date: "تا تاریخ",
    filters: "فیلترها",
  };
  if (labels[key]) return labels[key];

  const words: Record<string, string> = {
    id: "شناسه", product: "کالا", store: "فروشگاه", supplier: "تأمین‌کننده", customer: "مشتری",
    cashbox: "صندوق", inventory: "موجودی", batch: "بچ", quantity: "مقدار", remaining: "مانده",
    min: "حداقل", max: "حداکثر", total: "مجموع", average: "میانگین", purchase: "خرید",
    purchases: "خریدها", sale: "فروش", sales: "فروش‌ها", payment: "پرداخت", payments: "پرداخت‌ها",
    return: "برگشت", returns: "برگشت‌ها", adjustment: "تعدیل", adjustments: "تعدیلات",
    transaction: "تراکنش", transactions: "تراکنش‌ها", amount: "مبلغ", value: "ارزش", price: "قیمت",
    cost: "هزینه", profit: "سود", potential: "بالقوه", discount: "تخفیف", count: "تعداد",
    balance: "مانده", debt: "بدهی", credit: "بستانکاری", debit: "بدهکار", creditor: "بستانکار",
    debtor: "بدهکار", status: "وضعیت", type: "نوع", method: "روش", methods: "روش‌ها",
    date: "تاریخ", day: "روز", month: "ماه", year: "سال", created: "ایجاد", updated: "به‌روزرسانی",
    first: "اولین", last: "آخرین", opening: "ابتدای دوره", closing: "پایان دوره", description: "توضیحات",
    number: "شماره", invoice: "فاکتور", order: "سفارش", reference: "مرجع",
  };
  return key.split("_").map(part => words[part] || part).join(" ");
}

const DATE_KEY_PARTS = [
  "date", "_at", "_on", "day", "month", "year", "created", "updated",
  "last_purchase", "first_purchase", "last_payment", "first_payment",
];

function isDateKey(key: string) {
  const normalized = key.toLowerCase();
  return DATE_KEY_PARTS.some(part => normalized === part || normalized.includes(part));
}

function looksLikeIsoDate(value: string) {
  return /^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/.test(value);
}

function translateValue(value: string) {
  const normalized = value.trim().toLowerCase();
  const valueLabels: Record<string, string> = {
    debtor: "بدهکار", creditor: "بستانکار", settled: "تسویه‌شده", active: "فعال", inactive: "غیرفعال",
    cash: "نقدی", card: "کارتخوان", credit: "حسابی", purchase: "خرید", payment: "پرداخت",
    return: "برگشت", sale: "فروش", adjustment: "تعدیل", receipt: "دریافت", expense: "هزینه",
  };
  return valueLabels[normalized] || value;
}

function ReportData({ data }: { data: unknown }) {
  const isObject = !!data && typeof data === "object" && !Array.isArray(data);
  const payload = isObject ? data as Record<string, unknown> : null;
  const nestedItems = payload?.items;
  const rows = Array.isArray(nestedItems)
    ? nestedItems.filter((x): x is Record<string, unknown> => !!x && typeof x === "object")
    : normalizeRows(data);
  if (!rows.length) return <Box sx={{ py: 5, textAlign: "center" }}><Typography color="text.secondary">داده‌ای برای نمایش وجود ندارد.</Typography></Box>;
  const columns = Array.from(new Set(rows.flatMap(row => Object.keys(row))));
  const renderValue = (key: string, value: unknown) => {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "string") {
      if (isDateKey(key) && looksLikeIsoDate(value)) {
        const formatted = value.includes("T") || value.includes(" ") ? formatJalaliDateTime(value) : formatJalaliDate(value);
        return formatted;
      }
      return translateValue(value);
    }
    return typeof value === "object" ? JSON.stringify(value) : String(value);
  };
  const total = payload?.total_inventory_value ?? payload?.total_potential_profit;
  return <Stack spacing={2}>
    {total !== undefined && <Chip label={`${label(String(payload?.total_inventory_value !== undefined ? "total_inventory_value" : "total_potential_profit"))}: ${String(total)}`} color="primary" variant="outlined" sx={{ alignSelf: "flex-start", fontWeight: 700 }} />}
    <TableContainer sx={{ maxWidth: "100%", overflowX: "auto" }}><Table size="small" sx={{ minWidth: 650 }}><TableHead><TableRow>{columns.map(c => <TableCell key={c} sx={{ fontWeight: 800, whiteSpace: "nowrap" }}>{label(c)}</TableCell>)}</TableRow></TableHead><TableBody>{rows.map((row, index) => <TableRow hover key={String(row.id ?? row.inventory_id ?? row.product_id ?? index)}>{columns.map(c => <TableCell key={c} sx={{ whiteSpace: "nowrap" }}>{renderValue(c, row[c])}</TableCell>)}</TableRow>)}</TableBody></Table></TableContainer>
  </Stack>;
}

const groups = [
  { id: 0, title: "موجودی", icon: <InventoryIcon />, items: [
    ["کمبود موجودی", inventoryLowStock], ["ناموجود", inventoryOutOfStock], ["ارزش موجودی", inventoryValueReport],
    ["کالاهای کم‌گردش", inventorySlowMoving], ["سود بالقوه موجودی", inventoryPotentialProfit], ["خلاصه موجودی شعب", storeInventorySummary],
    ["گزارش کامل موجودی", fullInventoryReport], ["داشبورد موجودی", inventoryDashboard],
  ] as const },
  { id: 1, title: "تأمین‌کنندگان", icon: <LocalShippingIcon />, items: [
    ["بدهکاران تأمین‌کننده", supplierDebtors], ["گزارش خرید", supplierPurchaseReport], ["گزارش پرداخت", supplierPaymentReport],
    ["گزارش مانده", supplierBalanceReport], ["گزارش جامع", supplierComprehensiveReport],
  ] as const },
  { id: 2, title: "مشتریان", icon: <PeopleIcon />, items: [
    ["گزارش مشتریان", customerReport], ["بدهکاران", customerDebtors], ["بستانکاران", customerCreditors],
  ] as const },
  { id: 3, title: "مالی و صندوق", icon: <AccountBalanceIcon />, items: [
    ["خلاصه مالی", financialSummary], ["گزارش مالی", financialReport], ["دفتر صندوق", cashLedger],
    ["مانده صندوق‌ها", cashboxBalanceReport], ["گردش روزانه صندوق", dailyCashFlowReport],
  ] as const },
] as const;

type ReportFn = (filter?: ReportFilter) => Promise<unknown>;

export default function AdvancedReports() {
  const { activeStore } = useStore();
  const [group, setGroup] = useState(0);
  const [reportIndex, setReportIndex] = useState(0);
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const current = groups[group].items[reportIndex];
  const filter = useMemo(() => ({ store: activeStore?.id, start_date: start ? jalaliDateToIsoDate(start) : undefined, end_date: end ? jalaliDateToIsoDate(end) : undefined }), [activeStore?.id, start, end]);
  const load = async () => { if (!activeStore) return; setLoading(true); setError(""); try { setData(await (current[1] as ReportFn)(filter)); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } };
  useEffect(() => { setReportIndex(0); }, [group]);
  useEffect(() => { if (activeStore) void load(); }, [activeStore?.id, group, reportIndex]);
  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  const setRange = (kind: "today" | "month" | "all") => { if (kind === "all") { setStart(""); setEnd(""); return; } const now = new Date(); const j=toJalali(now.getFullYear(),now.getMonth()+1,now.getDate()); setEnd(formatJalali(j.jy,j.jm,j.jd)); setStart(kind === "today" ? todayJalali() : formatJalali(j.jy,j.jm,1)); };
  return <Box dir="rtl">
    <Stack direction={{ xs: "column", md: "row" }} className="page-header" sx={{ justifyContent: "space-between", gap: 1 }}>
      <Box><Typography variant="h5" sx={{ fontWeight: 800 }}>گزارش‌های تکمیلی</Typography><Typography color="text.secondary">دسترسی یکپارچه به گزارش‌های موجودی، تأمین‌کننده، مشتری و مالی</Typography></Box>
      <Button variant="contained" startIcon={<RefreshIcon />} onClick={() => void load()} disabled={loading}>به‌روزرسانی</Button>
    </Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card sx={{ mb: 2 }}><Tabs value={group} onChange={(_, value) => setGroup(value)} variant="scrollable" scrollButtons="auto">{groups.map(g => <Tab key={g.id} icon={g.icon} iconPosition="start" label={g.title} />)}</Tabs></Card>
    <Card sx={{ mb: 2 }}><CardContent><Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ alignItems: { md: "center" } }}><Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>{["امروز", "این ماه", "همه"].map((x, i) => <Button key={x} size="small" variant="outlined" onClick={() => setRange(i === 0 ? "today" : i === 1 ? "month" : "all")}>{x}</Button>)}</Stack><JalaliDateInput label="از تاریخ" value={start} onChange={setStart} allowClear /><JalaliDateInput label="تا تاریخ" value={end} onChange={setEnd} allowClear /><Button variant="outlined" onClick={() => void load()} disabled={loading}>اعمال</Button></Stack></CardContent></Card>
    <Card><CardContent><Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ mb: 2, alignItems: { md: "center" } }}><Typography sx={{ fontWeight: 800, flex: 1 }}>{current[0]}</Typography><Chip label={`${groups[group].items.length} گزارش در این بخش`} size="small" /></Stack><Divider sx={{ mb: 2 }} />
      <Tabs value={reportIndex} onChange={(_, value) => setReportIndex(value)} variant="scrollable" scrollButtons="auto" sx={{ mb: 2 }}>{groups[group].items.map(([title]) => <Tab key={title} label={title} />)}</Tabs>
      {loading ? <Box sx={{ py: 6, display: "grid", placeItems: "center" }}><CircularProgress /></Box> : <ReportData data={data} />}
    </CardContent></Card>
  </Box>;
}