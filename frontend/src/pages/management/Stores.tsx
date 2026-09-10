import { useEffect, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/AddBusiness";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStore } from "../../contexts/StoreContext";
import { createStore, deleteStore, listStores, updateStore, type ManagedStore } from "../../services/storeManagementService";

const errorMessage = (e: any) => e?.response?.data?.detail || e?.response?.data?.message || "عملیات انجام نشد.";

export default function Stores() {
  const { user, activeStore, setActiveStore } = useStore();
  const [items, setItems] = useState<ManagedStore[]>([]); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const [open, setOpen] = useState(false); const [editing, setEditing] = useState<ManagedStore | null>(null); const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", phone: "", address: "" });
  const isSuperuser = !!user?.is_superuser;
  const load = async () => { setLoading(true); setError(""); try { setItems(await listStores()); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  const openCreate = () => { setEditing(null); setForm({ name: "", code: "", phone: "", address: "" }); setOpen(true); };
  const openEdit = (s: ManagedStore) => { setEditing(s); setForm({ name: s.name, code: s.code, phone: s.phone || "", address: s.address || "" }); setOpen(true); };
  const save = async () => { if (!form.name.trim() || !form.code.trim()) return; setSaving(true); setError(""); try { const result = editing ? await updateStore(editing.id, form) : await createStore(form); if (activeStore?.id === result.id) setActiveStore({ ...activeStore, ...result }); setOpen(false); await load(); } catch (e) { setError(errorMessage(e)); } finally { setSaving(false); } };
  const toggle = async (s: ManagedStore) => { if (!isSuperuser) return; try { const result = await updateStore(s.id, { is_active: !s.is_active }); if (activeStore?.id === result.id && !result.is_active) { await load(); } else await load(); } catch (e) { setError(errorMessage(e)); } };
  const remove = async (s: ManagedStore) => { if (!isSuperuser || !window.confirm(`شعبه «${s.name}» حذف شود؟`)) return; try { await deleteStore(s.id); await load(); } catch (e) { setError(errorMessage(e)); } };

  return <Box dir="rtl"><Stack direction={{ xs: "column", sm: "row" }} sx={{ mb: 2, justifyContent: "space-between", gap: 1 }}><Box><Typography variant="h5" sx={{ fontWeight: 700 }}>مدیریت شعب</Typography><Typography variant="body2" color="text.secondary">اطلاعات و وضعیت شعبه‌های در دسترس</Typography></Box><Stack direction="row" spacing={1}><Button startIcon={<RefreshIcon />} variant="outlined" onClick={() => void load()}>به‌روزرسانی</Button>{isSuperuser && <Button startIcon={<AddIcon />} variant="contained" onClick={openCreate}>شعبه جدید</Button>}</Stack></Stack>
    {error && <Alert sx={{ mb: 2 }} severity="error" onClose={() => setError("")}>{error}</Alert>}
    <Card><CardContent>{loading ? <Box sx={{ minHeight: 240, display: "grid", placeItems: "center" }}><CircularProgress /></Box> : <TableContainer><Table><TableHead><TableRow><TableCell>شعبه</TableCell><TableCell>کد</TableCell><TableCell>مدیر</TableCell><TableCell>تلفن</TableCell><TableCell>وضعیت</TableCell><TableCell align="center">عملیات</TableCell></TableRow></TableHead><TableBody>{items.map(s => <TableRow key={s.id} hover><TableCell sx={{ fontWeight: 600 }}>{s.name}</TableCell><TableCell>{s.code}</TableCell><TableCell>{s.manager_username || "بدون مدیر"}</TableCell><TableCell>{s.phone || "-"}</TableCell><TableCell><Chip size="small" color={s.is_active ? "success" : "default"} label={s.is_active ? "فعال" : "غیرفعال"} /></TableCell><TableCell align="center"><IconButton title="ویرایش" onClick={() => openEdit(s)}><EditIcon /></IconButton>{isSuperuser && <IconButton title={s.is_active ? "غیرفعال کردن" : "فعال کردن"} onClick={() => void toggle(s)}><Chip size="small" label={s.is_active ? "غیرفعال" : "فعال"} /></IconButton>}{isSuperuser && <IconButton color="error" title="حذف" onClick={() => void remove(s)}><DeleteIcon /></IconButton>}</TableCell></TableRow>)}{!items.length && <TableRow><TableCell colSpan={6} align="center">شعبه‌ای یافت نشد.</TableCell></TableRow>}</TableBody></Table></TableContainer>}</CardContent></Card>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>{editing ? "ویرایش شعبه" : "ثبت شعبه جدید"}</DialogTitle><DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField label="نام شعبه" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /><TextField label="کد شعبه" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} required helperText="کد یکتا برای هر شعبه" /><TextField label="تلفن" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /><TextField label="آدرس" value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} multiline minRows={3} /></Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void save()} disabled={saving || !form.name.trim() || !form.code.trim()}>{saving ? "در حال ذخیره..." : "ذخیره"}</Button></DialogActions></Dialog>
  </Box>;
}
