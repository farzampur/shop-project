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
    id: "شناسه", product_name: "کالا", store_name: "فروشگاه", quantity: "مقدار", min_quantity: "حداقل",
    inventory_value: "ارزش موجودی", purchase_price: "قیمت خرید", sale_price: "قیمت فروش", total: "جمع",
    amount: "مبلغ", balance: "مانده", total_sales: "فروش", total_cost: "هزینه", total_profit: "سود",
    supplier_name: "تأمین‌کننده", customer_name: "مشتری", created_at: "تاریخ", transaction_type: "نوع تراکنش",
  };
  return labels[key] || key.replaceAll("_", " ");
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
    if (/(_at|_date|^date$|^day$|^month$|^year$)/i.test(key) && typeof value === "string") {
      const formatted = key.includes("_at") ? formatJalaliDateTime(value) : formatJalaliDate(value);
      return formatted;
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