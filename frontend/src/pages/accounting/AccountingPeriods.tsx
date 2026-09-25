import { useEffect, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import CloseIcon from "@mui/icons-material/Lock";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStore } from "../../contexts/StoreContext";
import { closePeriod, createPeriod, deletePeriod, listPeriods, updatePeriod, type AccountingPeriod } from "../../services/accountingService";
import { getApiErrorMessage } from "../../utils/apiError";
import { formatJalaliDate, jalaliDateToIsoDate } from "../../utils/jalaliDate";
import JalaliDateInput from "../../components/JalaliDateInput";

const empty = { name: "", start: "", end: "" };

export default function AccountingPeriods() {
  const { activeStore } = useStore();
  const [periods, setPeriods] = useState<AccountingPeriod[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<AccountingPeriod | null>(null);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const load = async () => { if (!activeStore) return; setError(""); try { setPeriods(await listPeriods(activeStore.id)); } catch (e) { setError(getApiErrorMessage(e, "بارگذاری دوره‌های مالی انجام نشد.")); } };
  useEffect(() => { void load(); }, [activeStore?.id]);
  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  const startCreate = () => { setEditing(null); setForm(empty); setOpen(true); };
  const startEdit = (period: AccountingPeriod) => { setEditing(period); setForm({ name: period.name, start: formatJalaliDate(period.start_date), end: formatJalaliDate(period.end_date) }); setOpen(true); };
  const save = async () => {
    const start_date = jalaliDateToIsoDate(form.start);
    const end_date = jalaliDateToIsoDate(form.end);
    if (!start_date || !end_date) { setError("تاریخ شروع و پایان را به‌صورت شمسی معتبر وارد کنید."); return; }
    try { setError(""); if (editing) await updatePeriod(editing.id, { name: form.name.trim(), start_date, end_date }); else await createPeriod({ store: activeStore.id, name: form.name.trim(), start_date, end_date }); setOpen(false); await load(); } catch (e) { setError(getApiErrorMessage(e, "ذخیره دوره مالی انجام نشد.")); }
  };
  const close = async (period: AccountingPeriod) => { if (!window.confirm(`بستن دوره «${period.name}» انجام شود؟ این عملیات قابل برگشت نیست.`)) return; try { setError(""); await closePeriod(period.id); await load(); } catch (e) { setError(getApiErrorMessage(e, "بستن دوره مالی انجام نشد.")); } };
  const remove = async (period: AccountingPeriod) => { if (!window.confirm(`حذف دوره «${period.name}» انجام شود؟`)) return; try { setError(""); await deletePeriod(period.id); await load(); } catch (e) { setError(getApiErrorMessage(e, "حذف دوره مالی انجام نشد.")); } };
  return <Box dir="rtl">
    <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 1, mb: 2 }}><Box><Typography variant="h5">دوره‌های مالی</Typography><Typography color="text.secondary">تعریف، ویرایش و بستن دوره‌های مالی فروشگاه جاری</Typography></Box><Stack direction="row" spacing={1}><Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => void load()}>به‌روزرسانی</Button><Button variant="contained" startIcon={<AddIcon />} onClick={startCreate}>دوره جدید</Button></Stack></Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card><CardContent><TableContainer><Table><TableHead><TableRow><TableCell>نام دوره</TableCell><TableCell>شروع</TableCell><TableCell>پایان</TableCell><TableCell>وضعیت</TableCell><TableCell>بسته‌شده در</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead><TableBody>{periods.map((period) => <TableRow key={period.id}><TableCell sx={{ fontWeight: 800 }}>{period.name}</TableCell><TableCell>{formatJalaliDate(period.start_date)}</TableCell><TableCell>{formatJalaliDate(period.end_date)}</TableCell><TableCell>{period.is_closed ? "بسته" : "باز"}</TableCell><TableCell>{period.closed_at ? formatJalaliDate(period.closed_at) : "—"}</TableCell><TableCell><Stack direction="row" spacing={0.5}>{!period.is_closed && <><Button size="small" startIcon={<EditIcon />} onClick={() => startEdit(period)}>ویرایش</Button><Button size="small" color="warning" startIcon={<CloseIcon />} onClick={() => void close(period)}>بستن</Button><Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => void remove(period)}>حذف</Button></>}</Stack></TableCell></TableRow>)}</TableBody></Table></TableContainer>{periods.length === 0 && <Typography sx={{ py: 4 }} color="text.secondary">دوره‌ای ثبت نشده است.</Typography>}</CardContent></Card>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>{editing ? "ویرایش دوره مالی" : "ایجاد دوره مالی"}</DialogTitle><DialogContent><Stack spacing={1.5} sx={{ pt: 1 }}><TextField label="نام دوره" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} autoFocus /><JalaliDateInput label="تاریخ شروع" value={form.start} onChange={(value) => setForm({ ...form, start: value })} /><JalaliDateInput label="تاریخ پایان" value={form.end} onChange={(value) => setForm({ ...form, end: value })} /></Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void save()} disabled={!form.name.trim() || !form.start || !form.end}>ذخیره</Button></DialogActions></Dialog>
  </Box>;
}
