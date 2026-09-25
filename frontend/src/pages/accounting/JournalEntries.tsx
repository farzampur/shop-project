import { Fragment, useEffect, useMemo, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, Collapse, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, MenuItem, Select, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import UndoIcon from "@mui/icons-material/Undo";
import { useStore } from "../../contexts/StoreContext";
import { createJournalEntry, listAccounts, listJournalEntries, reverseJournalEntry, type Account, type JournalEntry } from "../../services/accountingService";
import { getApiErrorMessage } from "../../utils/apiError";
import { formatJalaliDate, jalaliDateToIsoDate } from "../../utils/jalaliDate";
import JalaliDateInput from "../../components/JalaliDateInput";
import { money } from "./accountingUtils";

interface LineForm { account: string; debit: string; credit: string; description: string; }
const blankLine = (): LineForm => ({ account: "", debit: "", credit: "", description: "" });

export default function JournalEntries() {
  const { activeStore } = useStore();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState("");
  const [description, setDescription] = useState("");
  const [lines, setLines] = useState<LineForm[]>([blankLine(), blankLine()]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    if (!activeStore) return;
    setError("");
    try {
      const [entryRows, accountRows] = await Promise.all([
        listJournalEntries({ store: activeStore.id, start_date: start ? jalaliDateToIsoDate(start) : undefined, end_date: end ? jalaliDateToIsoDate(end) : undefined }),
        listAccounts(activeStore.id),
      ]);
      setEntries(entryRows); setAccounts(accountRows);
    } catch (e) { setError(getApiErrorMessage(e, "بارگذاری اسناد حسابداری انجام نشد.")); }
  };
  useEffect(() => { void load(); }, [activeStore?.id, start, end]);

  const leafAccounts = useMemo(() => accounts.filter((account) => !account.is_group && account.is_active), [accounts]);
  const debitTotal = lines.reduce((sum, line) => sum + (Number(line.debit) || 0), 0);
  const creditTotal = lines.reduce((sum, line) => sum + (Number(line.credit) || 0), 0);
  const balanced = Math.abs(debitTotal - creditTotal) < 0.005 && debitTotal > 0;

  const updateLine = (index: number, patch: Partial<LineForm>) => setLines((current) => current.map((line, i) => i === index ? { ...line, ...patch } : line));
  const removeLine = (index: number) => setLines((current) => current.length <= 2 ? current : current.filter((_, i) => i !== index));
  const submit = async () => {
    if (!activeStore) return;
    const entry_date = jalaliDateToIsoDate(date);
    if (!entry_date) { setError("تاریخ سند معتبر نیست."); return; }
    if (!balanced) { setError("جمع بدهکار و بستانکار باید برابر و بزرگ‌تر از صفر باشد."); return; }
    if (lines.some((line) => !line.account)) { setError("برای همه ردیف‌ها حساب انتخاب کنید."); return; }
    if (lines.some((line) => (Number(line.debit) > 0) === (Number(line.credit) > 0))) { setError("هر ردیف باید دقیقاً یکی از بدهکار یا بستانکار را داشته باشد."); return; }
    setSaving(true); setError("");
    try {
      await createJournalEntry({ store: activeStore.id, entry_date, description: description.trim(), lines: lines.map((line) => ({ account: Number(line.account), debit: line.debit || "0", credit: line.credit || "0", description: line.description.trim() })) });
      setOpen(false); setDate(""); setDescription(""); setLines([blankLine(), blankLine()]); await load();
    } catch (e) { setError(getApiErrorMessage(e, "ثبت سند انجام نشد.")); } finally { setSaving(false); }
  };
  const reverse = async (entry: JournalEntry) => {
    if (entry.status !== "posted") return;
    if (!window.confirm(`سند شماره ${entry.entry_number} برگشت شود؟`)) return;
    try { setError(""); await reverseJournalEntry(entry.id); await load(); } catch (e) { setError(getApiErrorMessage(e, "برگشت سند انجام نشد.")); }
  };
  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;

  return <Box dir="rtl">
    <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 1, mb: 2 }}><Box><Typography variant="h5">اسناد حسابداری</Typography><Typography color="text.secondary">ثبت، مشاهده و برگشت اسناد فروشگاه جاری</Typography></Box><Button variant="contained" startIcon={<AddIcon />} onClick={() => { setDate(formatJalaliDate(new Date())); setError(""); setOpen(true); }}>سند جدید</Button></Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card sx={{ mb: 2 }}><CardContent><Stack direction={{ xs: "column", md: "row" }} spacing={1}><JalaliDateInput label="از تاریخ" value={start} onChange={setStart} allowClear /><JalaliDateInput label="تا تاریخ" value={end} onChange={setEnd} allowClear /><Button startIcon={<RefreshIcon />} variant="outlined" onClick={() => void load()}>به‌روزرسانی</Button></Stack></CardContent></Card>
    <Card><CardContent><TableContainer><Table><TableHead><TableRow><TableCell width={40}> </TableCell><TableCell>شماره</TableCell><TableCell>تاریخ</TableCell><TableCell>شرح</TableCell><TableCell>وضعیت</TableCell><TableCell>مرجع</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead><TableBody>{entries.map((entry) => <Fragment key={entry.id}><TableRow hover><TableCell><IconButton size="small" onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}><ExpandMoreIcon sx={{ transform: expanded === entry.id ? "rotate(180deg)" : "none" }} /></IconButton></TableCell><TableCell sx={{ fontWeight: 800 }}>{new Intl.NumberFormat("fa-IR").format(entry.entry_number)}</TableCell><TableCell>{formatJalaliDate(entry.entry_date)}</TableCell><TableCell>{entry.description}</TableCell><TableCell><Chip size="small" label={entry.status === "posted" ? "ثبت قطعی" : "برگشت‌خورده"} color={entry.status === "posted" ? "success" : "warning"} /></TableCell><TableCell>{entry.source_type || "دستی"}</TableCell><TableCell>{entry.status === "posted" && !entry.reversal_of && <Button size="small" color="warning" startIcon={<UndoIcon />} onClick={() => void reverse(entry)}>برگشت</Button>}</TableCell></TableRow><TableRow><TableCell colSpan={7} sx={{ py: 0 }}><Collapse in={expanded === entry.id} unmountOnExit><Box sx={{ py: 1 }}><Table size="small"><TableHead><TableRow><TableCell>کد</TableCell><TableCell>حساب</TableCell><TableCell>شرح</TableCell><TableCell>بدهکار</TableCell><TableCell>بستانکار</TableCell></TableRow></TableHead><TableBody>{entry.line_items.map((line) => <TableRow key={line.id}><TableCell>{line.account_code}</TableCell><TableCell>{line.account_name}</TableCell><TableCell>{line.description || "—"}</TableCell><TableCell>{money(line.debit)}</TableCell><TableCell>{money(line.credit)}</TableCell></TableRow>)}</TableBody></Table></Box></Collapse></TableCell></TableRow></Fragment>)}</TableBody></Table></TableContainer>{entries.length === 0 && <Typography sx={{ py: 4 }} color="text.secondary">سندی برای نمایش وجود ندارد.</Typography>}</CardContent></Card>

    <Dialog open={open} onClose={() => !saving && setOpen(false)} fullWidth maxWidth="md"><DialogTitle>ثبت سند حسابداری</DialogTitle><DialogContent><Stack spacing={1.5} sx={{ pt: 1 }}><Stack direction={{ xs: "column", md: "row" }} spacing={1}><JalaliDateInput label="تاریخ سند" value={date} onChange={setDate} /><TextField label="شرح سند" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth /></Stack><TableContainer><Table size="small"><TableHead><TableRow><TableCell>حساب</TableCell><TableCell width={150}>بدهکار</TableCell><TableCell width={150}>بستانکار</TableCell><TableCell>شرح ردیف</TableCell><TableCell width={45}> </TableCell></TableRow></TableHead><TableBody>{lines.map((line, index) => <TableRow key={index}><TableCell><Select fullWidth value={line.account} displayEmpty onChange={(e) => updateLine(index, { account: String(e.target.value) })}><MenuItem value="">انتخاب حساب</MenuItem>{leafAccounts.map((account) => <MenuItem key={account.id} value={account.id}>{account.code} - {account.name}</MenuItem>)}</Select></TableCell><TableCell><TextField value={line.debit} onChange={(e) => updateLine(index, { debit: e.target.value, credit: e.target.value ? "" : line.credit })} slotProps={{ htmlInput: { inputMode: "decimal", dir: "ltr" } }} /></TableCell><TableCell><TextField value={line.credit} onChange={(e) => updateLine(index, { credit: e.target.value, debit: e.target.value ? "" : line.debit })} slotProps={{ htmlInput: { inputMode: "decimal", dir: "ltr" } }} /></TableCell><TableCell><TextField value={line.description} onChange={(e) => updateLine(index, { description: e.target.value })} /></TableCell><TableCell><IconButton size="small" color="error" disabled={lines.length <= 2} onClick={() => removeLine(index)}><Box component="span" sx={{ fontSize: 18, lineHeight: 1 }} aria-hidden="true">×</Box></IconButton></TableCell></TableRow>)}</TableBody></Table></TableContainer><Button size="small" onClick={() => setLines([...lines, blankLine()])}>افزودن ردیف</Button><Stack direction="row" spacing={2} sx={{ justifyContent: "flex-end" }}><Typography>جمع بدهکار: <strong>{money(debitTotal)}</strong></Typography><Typography>جمع بستانکار: <strong>{money(creditTotal)}</strong></Typography><Chip label={balanced ? "متوازن" : "نامتوازن"} color={balanced ? "success" : "error"} size="small" /></Stack></Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)} disabled={saving}>انصراف</Button><Button variant="contained" onClick={() => void submit()} disabled={saving || !date || !description.trim() || !balanced}>{saving ? "در حال ثبت..." : "ثبت سند"}</Button></DialogActions></Dialog>
  </Box>;
}
