import { useEffect, useMemo, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControl, FormControlLabel, InputLabel, MenuItem, Select, Stack, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStore } from "../../contexts/StoreContext";
import { createAccount, deleteAccount, listAccounts, updateAccount, type Account, type AccountType } from "../../services/accountingService";
import { getApiErrorMessage } from "../../utils/apiError";
import { ACCOUNT_TYPE_LABELS } from "./accountingUtils";

const emptyForm = { code: "", name: "", account_type: "asset" as AccountType, parent: "", is_group: false, is_active: true };

export default function ChartOfAccounts() {
  const { activeStore } = useStore();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Account | null>(null);
  const [form, setForm] = useState(emptyForm);

  const load = async () => {
    if (!activeStore) return;
    setLoading(true); setError("");
    try { setAccounts(await listAccounts(activeStore.id)); } catch (e) { setError(getApiErrorMessage(e, "بارگذاری سرفصل حساب‌ها انجام نشد.")); } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, [activeStore?.id]);

  const groups = useMemo(() => accounts.filter((account) => account.is_group && account.is_active), [accounts]);

  const startCreate = () => { setEditing(null); setForm(emptyForm); setOpen(true); };
  const startEdit = (account: Account) => {
    setEditing(account);
    setForm({ code: account.code, name: account.name, account_type: account.account_type, parent: account.parent ? String(account.parent) : "", is_group: account.is_group, is_active: account.is_active });
    setOpen(true);
  };
  const save = async () => {
    if (!activeStore) return;
    setError("");
    try {
      if (editing) {
        const payload = editing.is_system
          ? { name: form.name.trim(), is_active: form.is_active }
          : { code: form.code.trim(), name: form.name.trim(), account_type: form.account_type, parent: form.parent ? Number(form.parent) : null, is_group: form.is_group, is_active: form.is_active };
        await updateAccount(editing.id, payload);
      } else {
        await createAccount({ store: activeStore.id, code: form.code.trim(), name: form.name.trim(), account_type: form.account_type, parent: form.parent ? Number(form.parent) : null, is_group: form.is_group, is_active: form.is_active });
      }
      setOpen(false); await load();
    } catch (e) { setError(getApiErrorMessage(e, "ذخیره حساب انجام نشد.")); }
  };
  const remove = async (account: Account) => {
    if (!window.confirm(`حذف حساب «${account.name}» انجام شود؟`)) return;
    setError("");
    try { await deleteAccount(account.id); await load(); } catch (e) { setError(getApiErrorMessage(e, "حذف حساب انجام نشد.")); }
  };

  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  return <Box dir="rtl">
    <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 1, mb: 2 }}>
      <Box><Typography variant="h5">سرفصل حساب‌ها</Typography><Typography color="text.secondary">حساب‌های گروهی و تفصیلی فروشگاه جاری</Typography></Box>
      <Stack direction="row" spacing={1}><Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => void load()}>به‌روزرسانی</Button><Button variant="contained" startIcon={<AddIcon />} onClick={startCreate}>حساب جدید</Button></Stack>
    </Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card><CardContent><TableContainer><Table><TableHead><TableRow><TableCell>کد</TableCell><TableCell>نام</TableCell><TableCell>نوع</TableCell><TableCell>مادر</TableCell><TableCell>ماهیت</TableCell><TableCell>وضعیت</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead><TableBody>{accounts.map((account) => { const parent = accounts.find((x) => x.id === account.parent); return <TableRow key={account.id} hover><TableCell sx={{ fontWeight: 800 }}>{account.code}</TableCell><TableCell>{account.name}</TableCell><TableCell>{ACCOUNT_TYPE_LABELS[account.account_type]}</TableCell><TableCell>{parent ? `${parent.code} - ${parent.name}` : "—"}</TableCell><TableCell>{account.is_group ? "گروهی" : "برگ"}</TableCell><TableCell>{account.is_active ? "فعال" : "غیرفعال"}{account.is_system ? " · سیستمی" : ""}</TableCell><TableCell><Stack direction="row" spacing={0.5}><Button size="small" startIcon={<EditIcon />} onClick={() => startEdit(account)}>ویرایش</Button>{!account.is_system && <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => void remove(account)}>حذف</Button>}</Stack></TableCell></TableRow>; })}</TableBody></Table></TableContainer>{!loading && accounts.length === 0 && <Typography sx={{ py: 4 }} color="text.secondary">حسابی برای نمایش وجود ندارد.</Typography>}</CardContent></Card>

    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
      <DialogTitle>{editing ? "ویرایش حساب" : "ایجاد حساب جدید"}</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5} sx={{ pt: 1 }}>
          <TextField label="کد حساب" value={form.code} disabled={Boolean(editing?.is_system)} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <TextField label="نام حساب" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} autoFocus />
          <FormControl disabled={Boolean(editing?.is_system)}><InputLabel>نوع حساب</InputLabel><Select label="نوع حساب" value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value as AccountType })}>{Object.entries(ACCOUNT_TYPE_LABELS).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</Select></FormControl>
          <FormControl disabled={Boolean(editing?.is_system)}><InputLabel>حساب مادر</InputLabel><Select label="حساب مادر" value={form.parent} displayEmpty onChange={(e) => setForm({ ...form, parent: String(e.target.value) })}><MenuItem value="">بدون حساب مادر</MenuItem>{groups.filter((x) => x.id !== editing?.id).map((group) => <MenuItem key={group.id} value={group.id}>{group.code} - {group.name}</MenuItem>)}</Select></FormControl>
          <FormControlLabel control={<Checkbox checked={form.is_group} disabled={Boolean(editing?.is_system)} onChange={(e) => setForm({ ...form, is_group: e.target.checked })} />} label="حساب گروهی است" />
          <FormControlLabel control={<Checkbox checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />} label="حساب فعال است" />
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={() => setOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void save()} disabled={!form.code.trim() || !form.name.trim()}>ذخیره</Button></DialogActions>
    </Dialog>
  </Box>;
}
