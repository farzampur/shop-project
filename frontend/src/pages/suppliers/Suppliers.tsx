import { useEffect, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, IconButton, MenuItem, Stack, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { formatJalaliDateTime } from "../../utils/jalaliDate";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import HistoryIcon from "@mui/icons-material/History";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import PaymentIcon from "@mui/icons-material/Payment";
import { useStore } from "../../contexts/StoreContext";
import { listCashBoxes, type CashBox } from "../../services/cashboxService";
import {
  listSuppliers, createSupplier, updateSupplier, deleteSupplier, supplierLedger,
  supplierBalance, paySupplier, settleSupplier, type Supplier, type SupplierTx, type SupplierBalance,
} from "../../services/supplierService";

const money = (v: string | number | null | undefined) => Number(v || 0).toLocaleString("fa-IR");
const err = (e: any) => e?.response?.data?.detail || e?.response?.data?.message || "عملیات انجام نشد.";

export default function Suppliers() {
  const { activeStore, activeRole } = useStore();
  const [items, setItems] = useState<Supplier[]>([]);
  const [cashboxes, setCashboxes] = useState<CashBox[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [description, setDescription] = useState("");
  const [ledger, setLedger] = useState<SupplierTx[]>([]);
  const [ledgerTitle, setLedgerTitle] = useState("");
  const [balance, setBalance] = useState<SupplierBalance | null>(null);
  const [balanceTitle, setBalanceTitle] = useState("");
  const [paymentSupplier, setPaymentSupplier] = useState<Supplier | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentCashbox, setPaymentCashbox] = useState("");
  const [paymentDescription, setPaymentDescription] = useState("");
  const [settleSupplierTarget, setSettleSupplierTarget] = useState<Supplier | null>(null);
  const [settleCashbox, setSettleCashbox] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    if (!activeStore) return;
    setLoading(true);
    setError("");
    try {
      const [suppliers, boxes] = await Promise.all([
        listSuppliers(activeStore.id),
        listCashBoxes(activeStore.id),
      ]);
      setItems(suppliers);
      setCashboxes(boxes);
    } catch (e) {
      setError(err(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [activeStore?.id]);

  const form = (s?: Supplier) => {
    setEditing(s || null);
    setName(s?.name || "");
    setPhone(s?.phone || "");
    setAddress(s?.address || "");
    setDescription(s?.description || "");
    setOpen(true);
  };

  const save = async () => {
    if (!activeStore || !name.trim()) return;
    try {
      if (editing) await updateSupplier(editing.id, { name, phone, address, description });
      else await createSupplier({ store: activeStore.id, name, phone, address, description });
      setOpen(false);
      await load();
    } catch (e) { setError(err(e)); }
  };

  const showLedger = async (s: Supplier) => {
    try {
      const data = await supplierLedger(s.id);
      setLedger(Array.isArray(data) ? data : data.results);
      setLedgerTitle(s.name);
    } catch (e) { setError(err(e)); }
  };

  const showBalance = async (s: Supplier) => {
    try {
      setBalance(await supplierBalance(s.id));
      setBalanceTitle(s.name);
    } catch (e) { setError(err(e)); }
  };

  const openPayment = async (s: Supplier) => {
    setPaymentSupplier(s);
    setPaymentAmount("");
    setPaymentDescription("");
    setPaymentCashbox(cashboxes[0] ? String(cashboxes[0].id) : "");
    try {
      const b = await supplierBalance(s.id);
      setBalance(b);
    } catch (e) { setError(err(e)); }
  };

  const submitPayment = async () => {
    if (!paymentSupplier || !paymentCashbox) return;
    const amount = Number(paymentAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError("مبلغ پرداخت باید بیشتر از صفر باشد.");
      return;
    }
    const debt = Number(balance?.balance || 0);
    if (debt > 0 && amount > debt) {
      setError("مبلغ پرداخت بیشتر از بدهی تأمین‌کننده است.");
      return;
    }
    setActionLoading(true);
    setError("");
    try {
      await paySupplier({
        supplier: paymentSupplier.id,
        amount,
        cashbox: Number(paymentCashbox),
        description: paymentDescription || undefined,
      });
      setPaymentSupplier(null);
      await load();
    } catch (e) { setError(err(e)); }
    finally { setActionLoading(false); }
  };

  const openSettle = async (s: Supplier) => {
    setSettleSupplierTarget(s);
    setSettleCashbox(cashboxes[0] ? String(cashboxes[0].id) : "");
    try {
      const b = await supplierBalance(s.id);
      setBalance(b);
    } catch (e) { setError(err(e)); }
  };

  const submitSettle = async () => {
    if (!settleSupplierTarget || !settleCashbox) return;
    setActionLoading(true);
    setError("");
    try {
      await settleSupplier(settleSupplierTarget.id, Number(settleCashbox));
      setSettleSupplierTarget(null);
      await load();
    } catch (e) { setError(err(e)); }
    finally { setActionLoading(false); }
  };

  const remove = async (s: Supplier) => {
    if (activeRole !== "manager" || !confirm(`تأمین‌کننده «${s.name}» حذف شود؟`)) return;
    try { await deleteSupplier(s.id); await load(); } catch (e) { setError(err(e)); }
  };

  if (!activeStore) return <Alert severity="warning">ابتدا فروشگاه را انتخاب کنید.</Alert>;

  const canPay = activeRole === "manager" || activeRole === "cashier";
  const availableCashboxes = cashboxes.filter((c) => Number(c.balance) > 0);

  return (
    <Box dir="rtl">
      <Stack direction="row" className="page-header" sx={{ mb: 0, justifyContent: "space-between", alignItems: "center" }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>تأمین‌کنندگان</Typography>
          <Typography color="text.secondary">مدیریت طرف حساب خرید و بدهی تأمین‌کنندگان</Typography>
        </Box>
        <Box className="page-header-actions">
          <Button startIcon={<AddIcon />} variant="contained" onClick={() => form()}>تأمین‌کننده جدید</Button>
        </Box>
      </Stack>

      {error && <Alert sx={{ mb: 2 }} severity="error" onClose={() => setError("")}>{error}</Alert>}

      {loading ? <CircularProgress /> : (
        <Card>
          <CardContent>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>نام</TableCell><TableCell>تلفن</TableCell><TableCell>آدرس</TableCell><TableCell>عملیات</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((s) => (
                    <TableRow key={s.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{s.name}</TableCell>
                      <TableCell>{s.phone || "-"}</TableCell>
                      <TableCell>{s.address || "-"}</TableCell>
                      <TableCell>
                        <IconButton size="small" title="گردش حساب" onClick={() => void showLedger(s)}><HistoryIcon /></IconButton>
                        <IconButton size="small" title="مانده حساب" onClick={() => void showBalance(s)}><AccountBalanceIcon /></IconButton>
                        {canPay && <IconButton size="small" title="پرداخت" onClick={() => void openPayment(s)}><PaymentIcon /></IconButton>}
                        {canPay && <Button size="small" variant="outlined" sx={{ mx: 0.5 }} onClick={() => void openSettle(s)}>تسویه</Button>}
                        <IconButton size="small" title="ویرایش" onClick={() => form(s)}><EditIcon /></IconButton>
                        {activeRole === "manager" && <IconButton size="small" color="error" title="حذف" onClick={() => void remove(s)}><DeleteIcon /></IconButton>}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!items.length && <TableRow><TableCell colSpan={4} align="center">تأمین‌کننده‌ای ثبت نشده است.</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? "ویرایش تأمین‌کننده" : "ثبت تأمین‌کننده"}</DialogTitle>
        <DialogContent><Stack spacing={2} sx={{ mt: 1 }}>
          <TextField label="نام" value={name} onChange={(e) => setName(e.target.value)} required />
          <TextField label="تلفن" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <TextField label="آدرس" value={address} onChange={(e) => setAddress(e.target.value)} />
          <TextField label="توضیحات" value={description} onChange={(e) => setDescription(e.target.value)} multiline />
        </Stack></DialogContent>
        <DialogActions><Button onClick={() => setOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void save()}>ذخیره</Button></DialogActions>
      </Dialog>

      <Dialog open={!!ledgerTitle} onClose={() => setLedgerTitle("")} fullWidth maxWidth="md">
        <DialogTitle>گردش حساب {ledgerTitle}</DialogTitle>
        <DialogContent><Table size="small"><TableHead><TableRow><TableCell>نوع</TableCell><TableCell>مبلغ</TableCell><TableCell>شرح</TableCell><TableCell>تاریخ</TableCell></TableRow></TableHead>
          <TableBody>{ledger.map((t) => <TableRow key={t.id}><TableCell><Chip label={t.transaction_type === "purchase" ? "خرید" : t.transaction_type === "payment" ? "پرداخت" : "برگشت"} /></TableCell><TableCell>{money(t.amount)}</TableCell><TableCell>{t.description || "-"}</TableCell><TableCell>{formatJalaliDateTime(t.created_at)}</TableCell></TableRow>)}</TableBody>
        </Table></DialogContent>
      </Dialog>

      <Dialog open={!!balanceTitle} onClose={() => setBalanceTitle("")} fullWidth maxWidth="xs">
        <DialogTitle>مانده حساب {balanceTitle}</DialogTitle>
        <DialogContent><Stack spacing={1.5} sx={{ py: 1 }}>
          <Typography>جمع خرید: {money(balance?.purchases)}</Typography>
          <Typography>جمع پرداخت: {money(balance?.payments)}</Typography>
          <Typography>جمع برگشت: {money(balance?.returns)}</Typography>
          <Typography sx={{ fontWeight: 700 }}>مانده: {money(balance?.balance)}</Typography>
        </Stack></DialogContent>
      </Dialog>

      <Dialog open={!!paymentSupplier} onClose={() => !actionLoading && setPaymentSupplier(null)} fullWidth maxWidth="sm">
        <DialogTitle>پرداخت به {paymentSupplier?.name}</DialogTitle>
        <DialogContent><Stack spacing={2} sx={{ mt: 1 }}>
          <Typography color="text.secondary">بدهی فعلی: {money(balance?.balance)}</Typography>
          <TextField label="مبلغ پرداخت" type="number" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} slotProps={{ htmlInput: { min: 0, step: "0.01" } }} required />
          <TextField select label="صندوق پرداخت" value={paymentCashbox} onChange={(e) => setPaymentCashbox(e.target.value)} required>
            {availableCashboxes.map((c) => <MenuItem key={c.id} value={c.id}>{c.name} — {money(c.balance)}</MenuItem>)}
          </TextField>
          {!availableCashboxes.length && <Alert severity="warning">صندوق دارای موجودی برای پرداخت پیدا نشد.</Alert>}
          <TextField label="شرح" value={paymentDescription} onChange={(e) => setPaymentDescription(e.target.value)} />
        </Stack></DialogContent>
        <DialogActions><Button disabled={actionLoading} onClick={() => setPaymentSupplier(null)}>انصراف</Button><Button variant="contained" disabled={actionLoading || !availableCashboxes.length} onClick={() => void submitPayment()}>{actionLoading ? "در حال ثبت..." : "ثبت پرداخت"}</Button></DialogActions>
      </Dialog>

      <Dialog open={!!settleSupplierTarget} onClose={() => !actionLoading && setSettleSupplierTarget(null)} fullWidth maxWidth="sm">
        <DialogTitle>تسویه کامل {settleSupplierTarget?.name}</DialogTitle>
        <DialogContent><Stack spacing={2} sx={{ mt: 1 }}>
          <Typography>مبلغ تسویه: <strong>{money(balance?.balance)}</strong></Typography>
          <TextField select label="صندوق پرداخت" value={settleCashbox} onChange={(e) => setSettleCashbox(e.target.value)} required>
            {availableCashboxes.map((c) => <MenuItem key={c.id} value={c.id}>{c.name} — {money(c.balance)}</MenuItem>)}
          </TextField>
          {!availableCashboxes.length && <Alert severity="warning">صندوق دارای موجودی برای تسویه پیدا نشد.</Alert>}
          {Number(balance?.balance || 0) <= 0 && <Alert severity="info">حساب این تأمین‌کننده در حال حاضر تسویه است.</Alert>}
        </Stack></DialogContent>
        <DialogActions><Button disabled={actionLoading} onClick={() => setSettleSupplierTarget(null)}>انصراف</Button><Button variant="contained" disabled={actionLoading || !availableCashboxes.length || Number(balance?.balance || 0) <= 0} onClick={() => void submitSettle()}>{actionLoading ? "در حال تسویه..." : "تسویه کامل"}</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
