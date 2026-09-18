import { useEffect, useMemo, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, Stack, Table, TextField, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import AssessmentIcon from "@mui/icons-material/Assessment";
import PaymentIcon from "@mui/icons-material/Payment";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStore } from "../../contexts/StoreContext";
import { createCustomer, createCustomerPayment, deleteCustomer, getCustomerBalance, getCustomerLedger, getCustomerCreditors, getCustomerDebtors, getCustomerReport, listCustomers, updateCustomer, type Customer, type CustomerBalance, type CustomerCreditorRow, type CustomerDebtorRow, type CustomerLedger, type CustomerReportRow } from "../../services/customerService";
import { listCashBoxes, type CashBox } from "../../services/cashboxService";
import CustomerForm, { type CustomerFormState } from "./CustomerForm";

const money = (v: string | number) => Number(v || 0).toLocaleString("fa-IR");
const errorMessage = (e: any) => e?.response?.data?.detail || e?.response?.data?.message || (typeof e?.response?.data === "string" ? e.response.data : "عملیات انجام نشد.");

const emptyForm: CustomerFormState = { first_name: "", last_name: "", mobile: "", address: "" };

export default function Customers() {
  const { activeStore, activeRole } = useStore();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [cashboxes, setCashboxes] = useState<CashBox[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<CustomerFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [selected, setSelected] = useState<Customer | null>(null);
  const [balance, setBalance] = useState<CustomerBalance | null>(null);
  const [ledger, setLedger] = useState<CustomerLedger | null>(null);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentCashbox, setPaymentCashbox] = useState("");
  const [paymentDescription, setPaymentDescription] = useState("");
  const [reportOpen, setReportOpen] = useState(false);
  const [reportType, setReportType] = useState<"summary" | "debtors" | "creditors">("summary");
  const [reportRows, setReportRows] = useState<CustomerReportRow[] | CustomerDebtorRow[] | CustomerCreditorRow[]>([]);
  const [reportLoading, setReportLoading] = useState(false);

  const canManagePayments = activeRole === "manager" || activeRole === "cashier";
  const canDelete = activeRole === "manager";

  const load = async () => {
    if (!activeStore) return;
    setLoading(true); setError("");
    try {
      const [rows, boxes] = await Promise.all([listCustomers(activeStore.id), canManagePayments ? listCashBoxes(activeStore.id) : Promise.resolve([])]);
      setCustomers(rows); setCashboxes(boxes);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, [activeStore?.id, activeRole]);

  const openReport = async (type: "summary" | "debtors" | "creditors") => {
    setReportType(type); setReportOpen(true); setReportRows([]); setReportLoading(true); setError("");
    try {
      const rows = type === "summary" ? await getCustomerReport(activeStore.id) : type === "debtors" ? await getCustomerDebtors(activeStore.id) : await getCustomerCreditors(activeStore.id);
      setReportRows(rows);
    } catch (e) { setError(errorMessage(e)); } finally { setReportLoading(false); }
  };

  const openCreate = () => { setEditing(null); setForm(emptyForm); setFormOpen(true); };
  const openEdit = (c: Customer) => { setEditing(c); setForm({ first_name: c.first_name, last_name: c.last_name, mobile: c.mobile, address: c.address || "" }); setFormOpen(true); };
  const save = async () => {
    if (!activeStore || !form.first_name.trim() || !form.mobile.trim()) return;
    setSaving(true); setError("");
    try {
      if (editing) {
        await updateCustomer(editing.id, form);
      } else await createCustomer({ ...form, store: activeStore.id });
      setFormOpen(false); await load();
    } catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  };
  const remove = async (c: Customer) => {
    if (!window.confirm(`مشتری «${c.first_name} ${c.last_name}» حذف شود؟`)) return;
    try { await deleteCustomer(c.id); await load(); } catch (e) { setError(errorMessage(e)); }
  };
  const inspect = async (c: Customer) => {
    setSelected(c); setBalance(null); setLedger(null); setError("");
    try { const [b, l] = await Promise.all([getCustomerBalance(c.id), getCustomerLedger(c.id)]); setBalance(b); setLedger(l); } catch (e) { setError(errorMessage(e)); }
  };
  const openPayment = (c: Customer) => { setSelected(c); setPaymentAmount(""); setPaymentCashbox(cashboxes[0]?.id ? String(cashboxes[0].id) : ""); setPaymentDescription(""); setPaymentOpen(true); };
  const pay = async () => {
    if (!selected || !paymentCashbox || Number(paymentAmount) <= 0) return;
    setSaving(true); setError("");
    try {
      await createCustomerPayment({ customer: selected.id, transaction_type: "payment", amount: Number(paymentAmount), cashbox: Number(paymentCashbox), description: paymentDescription });
      setPaymentOpen(false); await inspect(selected); await load();
    } catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  };

  const balanceLabel = useMemo(() => {
    if (!balance) return null;
    const n = Number(balance.balance);
    return <Chip label={n > 0 ? `بدهکار: ${money(n)}` : n < 0 ? `بستانکار: ${money(Math.abs(n))}` : "تسویه"} color={n > 0 ? "error" : n < 0 ? "info" : "success"} />;
  }, [balance]);

  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;
  return <Box dir="rtl">
    <Stack direction={{ xs: "column", sm: "row" }} className="page-header" sx={{ mb: 0, justifyContent: "space-between", gap: 1 }}>
      <Box><Typography variant="h5" sx={{ fontWeight: 700 }}>مدیریت مشتریان</Typography><Typography variant="body2" color="text.secondary">دفتر مشتری، مانده حساب و دریافت مطالبات</Typography></Box>
      <Stack className="page-header-actions" direction="row" spacing={1} sx={{ flexWrap: "wrap" }}><Button size="small" startIcon={<AssessmentIcon />} variant="outlined" onClick={() => void openReport("summary")}>گزارش مشتریان</Button><Button size="small" variant="outlined" onClick={() => void openReport("debtors")}>بدهکاران</Button><Button size="small" variant="outlined" onClick={() => void openReport("creditors")}>بستانکاران</Button><Button size="small" startIcon={<RefreshIcon />} variant="outlined" onClick={() => void load()}>به‌روزرسانی</Button><Button size="small" startIcon={<AddIcon />} variant="contained" onClick={openCreate}>مشتری جدید</Button></Stack>
    </Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>{error}</Alert>}
    <Card><CardContent>
      {loading ? <Box sx={{ display: "grid", placeItems: "center", minHeight: 260 }}><CircularProgress /></Box> : <TableContainer><Table><TableHead><TableRow><TableCell>نام</TableCell><TableCell>موبایل</TableCell><TableCell>مانده حساب</TableCell><TableCell>آدرس</TableCell><TableCell align="center">عملیات</TableCell></TableRow></TableHead><TableBody>
        {customers.map(c => <CustomerRow key={c.id} customer={c} onInspect={() => void inspect(c)} onEdit={() => openEdit(c)} onDelete={() => void remove(c)} onPayment={() => openPayment(c)} canDelete={canDelete} canManagePayments={canManagePayments} />)}
        {!customers.length && <TableRow><TableCell colSpan={5} align="center">مشتری ثبت نشده است.</TableCell></TableRow>}
      </TableBody></Table></TableContainer>}
    </CardContent></Card>

    <CustomerForm open={formOpen} editing={!!editing} form={form} saving={saving} onChange={setForm} onClose={() => setFormOpen(false)} onSubmit={() => void save()} />

    <Dialog open={!!selected && !paymentOpen} onClose={() => setSelected(null)} fullWidth maxWidth="md"><DialogTitle>{selected ? `دفتر مشتری: ${selected.first_name} ${selected.last_name}` : ""}</DialogTitle><DialogContent>{balance && <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}><Card variant="outlined" sx={{ flex: 1 }}><CardContent><Typography variant="caption">کل فروش حسابی</Typography><Typography variant="h6">{money(balance.sales)}</Typography></CardContent></Card><Card variant="outlined" sx={{ flex: 1 }}><CardContent><Typography variant="caption">کل دریافتی</Typography><Typography variant="h6">{money(balance.payments)}</Typography></CardContent></Card><Card variant="outlined" sx={{ flex: 1 }}><CardContent><Typography variant="caption">مانده</Typography><Typography variant="h6">{balanceLabel}</Typography></CardContent></Card></Stack>}{ledger && <TableContainer><Table size="small"><TableHead><TableRow><TableCell>تاریخ</TableCell><TableCell>نوع</TableCell><TableCell>مبلغ</TableCell><TableCell>شرح</TableCell><TableCell>مانده</TableCell></TableRow></TableHead><TableBody>{ledger.transactions.map(t => <TableRow key={t.id}><TableCell>{t.date}</TableCell><TableCell>{t.type === "sale" ? "فروش" : "دریافت"}</TableCell><TableCell>{money(t.amount)}</TableCell><TableCell>{t.description || "-"}</TableCell><TableCell>{money(t.balance)}</TableCell></TableRow>)}</TableBody></Table></TableContainer>}</DialogContent><DialogActions>{canManagePayments && <Button startIcon={<PaymentIcon />} variant="contained" onClick={() => selected && openPayment(selected)}>ثبت دریافت</Button>}<Button onClick={() => setSelected(null)}>بستن</Button></DialogActions></Dialog>

    <Dialog open={reportOpen} onClose={() => setReportOpen(false)} fullWidth maxWidth="md"><DialogTitle>{reportType === "summary" ? "گزارش مشتریان" : reportType === "debtors" ? "مشتریان بدهکار" : "مشتریان بستانکار"}</DialogTitle><DialogContent>{reportLoading ? <Box sx={{ display: "grid", placeItems: "center", minHeight: 180 }}><CircularProgress /></Box> : <TableContainer><Table size="small"><TableHead><TableRow>{reportType === "summary" ? <><TableCell>مشتری</TableCell><TableCell>موبایل</TableCell><TableCell>تعداد خرید</TableCell><TableCell>مجموع خرید</TableCell><TableCell>آخرین خرید</TableCell></> : <><TableCell>مشتری</TableCell><TableCell>{reportType === "debtors" ? "مبلغ بدهی" : "مبلغ بستانکاری"}</TableCell><TableCell align="center">دفتر حساب</TableCell></>}</TableRow></TableHead><TableBody>{reportRows.map((row) => reportType === "summary" ? <TableRow key={(row as CustomerReportRow).id}><TableCell>{(row as CustomerReportRow).name}</TableCell><TableCell>{(row as CustomerReportRow).mobile}</TableCell><TableCell>{(row as CustomerReportRow).order_count}</TableCell><TableCell>{money((row as CustomerReportRow).total_purchase)}</TableCell><TableCell>{(row as CustomerReportRow).last_order_date || "-"}</TableCell></TableRow> : <TableRow key={(row as CustomerDebtorRow).customer_id}><TableCell>{(row as CustomerDebtorRow | CustomerCreditorRow).customer_name}</TableCell><TableCell>{money(reportType === "debtors" ? (row as CustomerDebtorRow).balance : (row as CustomerCreditorRow).credit)}</TableCell><TableCell align="center"><Button size="small" onClick={() => { const id = (row as CustomerDebtorRow | CustomerCreditorRow).customer_id; const c = customers.find(x => x.id === id); if (c) { setReportOpen(false); void inspect(c); } }}>مشاهده</Button></TableCell></TableRow>)}{!reportRows.length && <TableRow><TableCell colSpan={reportType === "summary" ? 5 : 3} align="center">موردی یافت نشد.</TableCell></TableRow>}</TableBody></Table></TableContainer>}</DialogContent><DialogActions><Button onClick={() => setReportOpen(false)}>بستن</Button></DialogActions></Dialog>

    <Dialog open={paymentOpen} onClose={() => setPaymentOpen(false)} fullWidth maxWidth="sm"><DialogTitle>دریافت از مشتری</DialogTitle><DialogContent><Stack spacing={2} sx={{ mt: 1 }}><Typography>{selected ? `${selected.first_name} ${selected.last_name}` : ""}</Typography><TextField label="مبلغ" type="number" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} /><TextField select slotProps={{ select: { native: true } }} label="صندوق" value={paymentCashbox} onChange={e => setPaymentCashbox(e.target.value)}><option value="">انتخاب صندوق</option>{cashboxes.map(b => <option key={b.id} value={b.id}>{b.name} — {money(b.balance)}</option>)}</TextField><TextField label="شرح" value={paymentDescription} onChange={e => setPaymentDescription(e.target.value)} /></Stack></DialogContent><DialogActions><Button onClick={() => setPaymentOpen(false)}>انصراف</Button><Button variant="contained" onClick={() => void pay()} disabled={saving || Number(paymentAmount) <= 0 || !paymentCashbox}>ثبت دریافت</Button></DialogActions></Dialog>
  </Box>;
}

function CustomerRow({ customer, onInspect, onEdit, onDelete, onPayment, canDelete, canManagePayments }: { customer: Customer; onInspect: () => void; onEdit: () => void; onDelete: () => void; onPayment: () => void; canDelete: boolean; canManagePayments: boolean }) {
  const [b, setB] = useState<CustomerBalance | null>(null);
  useEffect(() => { void getCustomerBalance(customer.id).then(setB).catch(() => undefined); }, [customer.id]);
  const n = Number(b?.balance || 0);
  return <TableRow hover><TableCell><Typography sx={{ fontWeight: 600 }}>{customer.first_name} {customer.last_name}</Typography></TableCell><TableCell>{customer.mobile}</TableCell><TableCell>{n > 0 ? <Chip size="small" color="error" label={`بدهکار ${money(n)}`} /> : n < 0 ? <Chip size="small" color="info" label={`بستانکار ${money(Math.abs(n))}`} /> : <Chip size="small" color="success" label="تسویه" />}</TableCell><TableCell>{customer.address || "-"}</TableCell><TableCell align="center"><Stack direction="row" sx={{ justifyContent: "center" }}><IconButton title="دفتر حساب" onClick={onInspect}><ReceiptLongIcon /></IconButton>{canManagePayments && <IconButton title="ثبت دریافت" onClick={onPayment}><PaymentIcon /></IconButton>}<IconButton title="ویرایش" onClick={onEdit}><EditIcon /></IconButton>{canDelete && <IconButton color="error" title="حذف" onClick={onDelete}><DeleteIcon /></IconButton>}</Stack></TableCell></TableRow>;
}
