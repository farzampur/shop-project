import { useEffect, useMemo, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, IconButton, MenuItem, Stack, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/PersonAdd";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStore } from "../../contexts/StoreContext";
import { createManagedUser, deleteManagedUser, listManagedUsers, updateManagedUser, type ManagedUser } from "../../services/userManagementService";
import type { StoreRole } from "../../services/authTypes";

const roles: { value: StoreRole; label: string }[] = [
  { value: "manager", label: "مدیر فروشگاه" },
  { value: "seller", label: "فروشنده" },
  { value: "cashier", label: "صندوقدار" },
  { value: "warehouse", label: "انباردار" },
];
const errorMessage = (e: any) => e?.response?.data?.detail || e?.response?.data?.message || "عملیات انجام نشد.";

export default function Users() {
  const { activeStore, activeRole, user } = useStore();
  const [items, setItems] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ManagedUser | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", first_name: "", last_name: "", email: "", role: "seller" as StoreRole });

  const canManage = activeRole === "manager" || user?.is_superuser;
  const load = async () => {
    if (!activeStore || !canManage) return;
    setLoading(true); setError("");
    try { setItems(await listManagedUsers(activeStore.id)); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, [activeStore?.id, activeRole, user?.is_superuser]);

  const openCreate = () => { setEditing(null); setForm({ username: "", password: "", first_name: "", last_name: "", email: "", role: "seller" }); setOpen(true); };
  const openEdit = (item: ManagedUser) => { setEditing(item); setForm({ username: item.username, password: "", first_name: item.first_name, last_name: item.last_name, email: item.email, role: item.role }); setOpen(true); };
  const save = async () => {
    if (!activeStore) return;
    setSaving(true); setError("");
    try {
      if (editing) await updateManagedUser(editing.id, { role: form.role, is_active: editing.is_active });
      else await createManagedUser({ username: form.username.trim(), password: form.password, first_name: form.first_name, last_name: form.last_name, email: form.email, role: form.role, store: activeStore.id });
      setOpen(false); await load();
    } catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  };
  const toggle = async (item: ManagedUser) => {
    if (item.user === user?.id) return;
    try { await updateManagedUser(item.id, { is_active: !item.is_active }); await load(); } catch (e) { setError(errorMessage(e)); }
  };
  const remove = async (item: ManagedUser) => {
    if (item.user === user?.id || !window.confirm(`دسترسی «${item.username}» از این شعبه حذف شود؟`)) return;
    try { await deleteManagedUser(item.id); await load(); } catch (e) { setError(errorMessage(e)); }
  };
  const title = useMemo(() => editing ? `ویرایش دسترسی ${editing.username}` : "کاربر جدید", [editing]);

  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  return <Box dir="rtl">
    <Stack direction={{ xs: "column", sm: "row" }} sx={{ mb: 2, justifyContent: "space-between", gap: 1 }}>
      <Box><Typography variant="h5" sx={{ fontWeight: 700 }}>کاربران و کارکنان</Typography><Typography variant="body2" color="text.secondary">مدیریت کاربران و سطح دسترسی شعبه «{activeStore.name}»</Typography></Box>
      <Stack direction="row" spacing={1}><Button startIcon={<RefreshIcon />} variant="outlined" onClick={() => void load()}>به‌روزرسانی</Button><Button startIcon={<AddIcon />} variant="contained" onClick={openCreate}>کاربر جدید</Button></Stack>
    </Stack>
    {error && <Alert sx={{ mb: 2 }} severity="error" onClose={() => setError("")}>{error}</Alert>}
    <Card><CardContent>{loading ? <Box sx={{ minHeight: 240, display: "grid", placeItems: "center" }}><CircularProgress /></Box> : <TableContainer><Table><TableHead><TableRow><TableCell>کاربر</TableCell><TableCell>ایمیل</TableCell><TableCell>نقش</TableCell><TableCell>وضعیت</TableCell><TableCell align="center">عملیات</TableCell></TableRow></TableHead><TableBody>
      {items.map(item => <TableRow key={item.id} hover><TableCell><Typography sx={{ fontWeight: 600 }}>{item.first_name || item.last_name ? `${item.first_name} ${item.last_name}`.trim() : item.username}</Typography><Typography variant="caption" color="text.secondary">@{item.username}</Typography></TableCell><TableCell>{item.email || "-"}</TableCell><TableCell><Chip size="small" label={item.role_display} /></TableCell><TableCell><Chip size="small" color={item.is_active ? "success" : "default"} label={item.is_active ? "فعال" : "غیرفعال"} /></TableCell><TableCell align="center"><IconButton title="ویرایش نقش" onClick={() => openEdit(item)}><EditIcon /></IconButton>{item.user !== user?.id && <IconButton title={item.is_active ? "غیرفعال کردن" : "فعال کردن"} onClick={() => void toggle(item)}><Chip size="small" label={item.is_active ? "غیرفعال" : "فعال"} /></IconButton>}{item.user !== user?.id && <IconButton color="error" title="حذف دسترسی شعبه" onClick={() => void remove(item)}><DeleteIcon /></IconButton>}</TableCell></TableRow>)}
      {!items.length && <TableRow><TableCell colSpan={5} align="center">کاربری برای این شعبه ثبت نشده است.</TableCell></TableRow>}
    </TableBody></Table></TableContainer>}</CardContent></Card>

    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>{title}</DialogTitle><DialogContent><Stack spacing={2} sx={{ mt: 1 }}>
      {!editing && <><TextField label="نام کاربری" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required /><TextField label="رمز عبور" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required helperText="حداقل ۶ کاراکتر" /><TextField label="نام" value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} /><TextField label="نام خانوادگی" value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} /><TextField label="ایمیل" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></>}
      <TextField select label="نقش" value={form.role} onChange={e => setForm({ ...form, role: e.target.value as StoreRole })}>{roles.map(r => <MenuItem key={r.value} value={r.value}>{r.label}</MenuItem>)}</TextField>
      {editing && <Alert severity="info">تغییر اطلاعات شخصی و رمز عبور از این صفحه انجام نمی‌شود؛ این صفحه فقط دسترسی شعبه را مدیریت می‌کند.</Alert>}
    </Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void save()} disabled={saving || (!editing && (!form.username.trim() || form.password.length < 6))}>{saving ? "در حال ذخیره..." : "ذخیره"}</Button></DialogActions></Dialog>
  </Box>;
}
