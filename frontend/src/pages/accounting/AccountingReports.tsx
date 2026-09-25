import { useEffect, useMemo, useState } from "react";
import { Alert, Box, Card, CardContent, Chip, CircularProgress, FormControl, InputLabel, MenuItem, Select, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Tab, Typography } from "@mui/material";
import { useStore } from "../../contexts/StoreContext";
import { getBalanceSheet, getGeneralLedger, getProfitLoss, getTrialBalance, listAccounts, type Account, type BalanceSheetReport, type GeneralLedgerRow, type ProfitLossReport, type TrialBalanceRow } from "../../services/accountingService";
import { getApiErrorMessage } from "../../utils/apiError";
import { jalaliDateToIsoDate } from "../../utils/jalaliDate";
import JalaliDateInput from "../../components/JalaliDateInput";
import { money } from "./accountingUtils";

export default function AccountingReports() {
  const { activeStore } = useStore();
  const [tab, setTab] = useState(0);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [accountId, setAccountId] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [trial, setTrial] = useState<TrialBalanceRow[]>([]);
  const [ledger, setLedger] = useState<GeneralLedgerRow[]>([]);
  const [profit, setProfit] = useState<ProfitLossReport | null>(null);
  const [sheet, setSheet] = useState<BalanceSheetReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const filters = useMemo(() => ({ store: activeStore?.id ?? 0, start_date: start ? jalaliDateToIsoDate(start) : undefined, end_date: end ? jalaliDateToIsoDate(end) : undefined }), [activeStore?.id, start, end]);

  const load = async () => {
    if (!activeStore) return;
    setLoading(true); setError("");
    try {
      if (tab === 0) setTrial(await getTrialBalance(filters));
      else if (tab === 1) setLedger(await getGeneralLedger({ ...filters, account: accountId ? Number(accountId) : undefined }));
      else if (tab === 2) setProfit(await getProfitLoss(filters));
      else setSheet(await getBalanceSheet(activeStore.id, filters.end_date));
    } catch (e) { setError(getApiErrorMessage(e, "بارگذاری گزارش حسابداری انجام نشد.")); } finally { setLoading(false); }
  };
  useEffect(() => { if (activeStore) { void listAccounts(activeStore.id).then(setAccounts).catch(() => setAccounts([])); } }, [activeStore?.id]);
  useEffect(() => { void load(); }, [activeStore?.id, tab, start, end, accountId]);

  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  const renderTable = () => {
    if (tab === 0) return <TableContainer><Table><TableHead><TableRow><TableCell>کد</TableCell><TableCell>حساب</TableCell><TableCell>نوع</TableCell><TableCell>بدهکار</TableCell><TableCell>بستانکار</TableCell><TableCell>مانده</TableCell></TableRow></TableHead><TableBody>{trial.map((row) => <TableRow key={row.account_id}><TableCell>{row.account__code}</TableCell><TableCell>{row.account__name}</TableCell><TableCell>{row.account__account_type}</TableCell><TableCell>{money(row.debit)}</TableCell><TableCell>{money(row.credit)}</TableCell><TableCell>{money(row.balance)}</TableCell></TableRow>)}</TableBody></Table></TableContainer>;
    if (tab === 1) return <TableContainer><Table><TableHead><TableRow><TableCell>تاریخ</TableCell><TableCell>شماره سند</TableCell><TableCell>حساب</TableCell><TableCell>شرح</TableCell><TableCell>بدهکار</TableCell><TableCell>بستانکار</TableCell><TableCell>مانده</TableCell></TableRow></TableHead><TableBody>{ledger.map((row, index) => <TableRow key={`${row.entry_id}-${index}`}><TableCell>{row.date}</TableCell><TableCell>{row.entry_number}</TableCell><TableCell>{row.account_code} - {row.account_name}</TableCell><TableCell>{row.description}</TableCell><TableCell>{money(row.debit)}</TableCell><TableCell>{money(row.credit)}</TableCell><TableCell>{money(row.balance)}</TableCell></TableRow>)}</TableBody></Table></TableContainer>;
    if (tab === 2) return <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>{[["درآمد", profit?.revenue], ["هزینه", profit?.expense], ["سود خالص", profit?.net_profit]].map(([label, value]) => <Card key={String(label)} sx={{ flex: 1 }}><CardContent><Typography color="text.secondary">{label}</Typography><Typography variant="h5">{money(value as string | number)}</Typography></CardContent></Card>)}</Stack>;
    return <Stack spacing={1.5}>{sheet && <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}><Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary">دارایی</Typography><Typography variant="h6">{money(sheet.assets)}</Typography></CardContent></Card><Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary">بدهی</Typography><Typography variant="h6">{money(sheet.liabilities)}</Typography></CardContent></Card><Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary">حقوق مالکانه</Typography><Typography variant="h6">{money(sheet.equity)}</Typography></CardContent></Card><Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary">سود جاری</Typography><Typography variant="h6">{money(sheet.current_profit)}</Typography></CardContent></Card></Stack>}{sheet && <Chip label={sheet.balanced ? "ترازنامه متوازن است" : "ترازنامه نامتوازن است"} color={sheet.balanced ? "success" : "error"} sx={{ alignSelf: "flex-start" }} />}{sheet && <TableContainer><Table><TableHead><TableRow><TableCell>کد</TableCell><TableCell>حساب</TableCell><TableCell>مانده</TableCell></TableRow></TableHead><TableBody>{sheet.accounts.map((row) => <TableRow key={row.account_id}><TableCell>{row.account__code}</TableCell><TableCell>{row.account__name}</TableCell><TableCell>{money(row.balance)}</TableCell></TableRow>)}</TableBody></Table></TableContainer>}</Stack>;
  };

  return <Box dir="rtl"><Typography variant="h5" sx={{ mb: 0.5 }}>گزارش‌های حسابداری</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>گزارش‌ها مستقیماً از Backend حسابداری فروشگاه جاری خوانده می‌شوند.</Typography><Card sx={{ mb: 2 }}><CardContent><Stack direction={{ xs: "column", md: "row" }} spacing={1.5}><JalaliDateInput label="از تاریخ" value={start} onChange={setStart} allowClear /><JalaliDateInput label="تا تاریخ" value={end} onChange={setEnd} allowClear />{tab === 1 && <FormControl sx={{ minWidth: 250 }}><InputLabel>حساب</InputLabel><Select label="حساب" value={accountId} displayEmpty onChange={(e) => setAccountId(String(e.target.value))}><MenuItem value="">همه حساب‌ها</MenuItem>{accounts.filter((x) => !x.is_group && x.is_active).map((a) => <MenuItem key={a.id} value={a.id}>{a.code} - {a.name}</MenuItem>)}</Select></FormControl>}</Stack></CardContent></Card><Card><CardContent><Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable" scrollButtons="auto"><Tab label="تراز آزمایشی" /><Tab label="دفتر کل" /><Tab label="سود و زیان" /><Tab label="ترازنامه" /></Tabs><Box sx={{ pt: 2 }}>{error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}{loading ? <Box sx={{ py: 6, display: "grid", placeItems: "center" }}><CircularProgress /></Box> : renderTable()}</Box></CardContent></Card></Box>;
}
