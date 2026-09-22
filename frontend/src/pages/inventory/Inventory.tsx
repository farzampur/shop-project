import { useEffect, useMemo, useState } from "react";
import { getApiErrorMessage as err } from "../../utils/apiError";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog,
  DialogActions, DialogContent, DialogTitle, Stack, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
  Tabs, Tab, Paper,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import HistoryIcon from "@mui/icons-material/History";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import { useStore } from "../../contexts/StoreContext";
import {
  listInventory, listInventoryTransactions, updateInventoryMinimum, adjustInventory,
  type InventoryItem, type InventoryTransaction,
} from "../../services/inventoryService";
import { listProductBatches, type ProductBatch } from "../../services/batchService";

const money = (value: string) => Number(value).toLocaleString("fa-IR");

export default function Inventory() {
  const { activeStore, activeRole } = useStore();
  const [tab, setTab] = useState(0);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [batches, setBatches] = useState<ProductBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [error, setError] = useState("");
  const [edit, setEdit] = useState<InventoryItem | null>(null);
  const [min, setMin] = useState("");
  const [qty, setQty] = useState("");
  const [desc, setDesc] = useState("");
  const [history, setHistory] = useState<InventoryTransaction[]>([]);
  const [historyTitle, setHistoryTitle] = useState("");
  const [batchFilter, setBatchFilter] = useState<"active" | "empty">("active");
  const [activeBatches, setActiveBatches] = useState<ProductBatch[]>([]);

  const load = async () => {
    if (!activeStore) return;
    setLoading(true); setError("");
    try { setItems(await listInventory(activeStore.id)); }
    catch (e) { setError(err(e)); }
    finally { setLoading(false); }
  };

  const loadBatches = async () => {
    if (!activeStore) return;
    setBatchLoading(true); setError("");
    try { setBatches(await listProductBatches(activeStore.id, { remaining: batchFilter })); }
    catch (e) { setError(err(e)); }
    finally { setBatchLoading(false); }
  };

  useEffect(() => { void load(); }, [activeStore?.id]);
  useEffect(() => {
    if (!activeStore) return;
    void listProductBatches(activeStore.id, { remaining: "active" }).then(setActiveBatches).catch((e) => setError(err(e)));
  }, [activeStore?.id]);
  useEffect(() => { if (tab === 1) void loadBatches(); }, [activeStore?.id, tab, batchFilter]);

  const saveMin = async () => {
    if (!edit || !activeStore) return;
    try { await updateInventoryMinimum(edit.id, activeStore.id, min); setEdit(null); await load(); }
    catch (e) { setError(err(e)); }
  };

  const adjust = async () => {
    if (!edit || !qty) return;
    try { await adjustInventory(edit.id, qty, desc); setEdit(null); setQty(""); setDesc(""); await load(); }
    catch (e) { setError(err(e)); }
  };

  const showHistory = async (i: InventoryItem) => {
    if (!activeStore) return;
    try { setHistory(await listInventoryTransactions(activeStore.id, i.product)); setHistoryTitle(i.product_name); }
    catch (e) { setError(err(e)); }
  };

  const groupedBatchCount = useMemo(() => new Set(batches.map((b) => b.product)).size, [batches]);

  if (!activeStore) return <Alert severity="warning">ابتدا فروشگاه را انتخاب کنید.</Alert>;
  const low = items.filter((i) => Number(i.quantity) <= Number(i.min_quantity)).length;
  const batchRemainingByProduct = useMemo(() => {
    const result: Record<number, number> = {};
    for (const batch of activeBatches) result[batch.product] = (result[batch.product] || 0) + Number(batch.remaining_quantity);
    return result;
  }, [activeBatches]);

  return (
    <Box dir="rtl" className="page-shell">
      <Stack direction={{ xs: "column", sm: "row" }} className="page-header" sx={{ mb: 0, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, gap: 1 }}>
        <Box>
          <Typography variant="h5" className="soft-title">مدیریت موجودی</Typography>
          <Typography color="text.secondary">موجودی و بچ‌های کالا در فروشگاه {activeStore.name}</Typography>
        </Box>
        <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-start" }}>
          <Chip color={low ? "warning" : "success"} label={`${low} کالای نیازمند تأمین`} />
          <Chip color="secondary" variant="outlined" label={`${groupedBatchCount} کالا با بچ`} />
        </Stack>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>{error}</Alert>}

      <Paper className="section-card" sx={{ p: 0, overflow: "hidden" }}>
        <Tabs value={tab} onChange={(_, value) => setTab(value)} sx={{ px: 1, borderBottom: 1, borderColor: "divider" }}>
          <Tab icon={<Inventory2Icon fontSize="small" />} iconPosition="start" label="موجودی کالا" />
          <Tab icon={<Inventory2Icon fontSize="small" />} iconPosition="start" label="بچ‌های کالا" />
        </Tabs>

        {tab === 0 && (
          <Box sx={{ p: 1.5 }}>
            {loading ? <CircularProgress /> : (
              <Card variant="outlined">
                <CardContent sx={{ p: 0 }}>
                  <TableContainer>
                    <Table size="small">
                      <TableHead><TableRow>
                        <TableCell>کالا</TableCell><TableCell>بارکد</TableCell><TableCell>موجودی</TableCell>
                        <TableCell>حداقل</TableCell><TableCell>مانده بچ</TableCell><TableCell>وضعیت</TableCell><TableCell>عملیات</TableCell>
                      </TableRow></TableHead>
                      <TableBody>
                        {items.map((i) => {
                          const isLow = Number(i.quantity) <= Number(i.min_quantity);
                          return <TableRow key={i.id} hover>
                            <TableCell sx={{ fontWeight: 700 }}>{i.product_name}</TableCell>
                            <TableCell>{i.barcode || "-"}</TableCell><TableCell>{i.quantity}</TableCell>
                            <TableCell>{i.min_quantity}</TableCell>
                            <TableCell>{(batchRemainingByProduct[i.product] ?? 0).toLocaleString("fa-IR", { maximumFractionDigits: 3 })}</TableCell>
                            <TableCell><Chip size="small" color={isLow ? "warning" : "success"} label={isLow ? "نیازمند تأمین" : "مناسب"} /></TableCell>
                            <TableCell>
                              <Button size="small" startIcon={<HistoryIcon />} onClick={() => void showHistory(i)}>گردش</Button>
                              {activeRole && (activeRole === "manager" || activeRole === "warehouse") && <Button size="small" startIcon={<EditIcon />} onClick={() => { setEdit(i); setMin(i.min_quantity); setQty(i.quantity); setDesc(""); }}>تعدیل</Button>}
                            </TableCell>
                          </TableRow>;
                        })}
                        {!items.length && <TableRow><TableCell colSpan={7} align="center">موجودی‌ای ثبت نشده است.</TableCell></TableRow>}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            )}
          </Box>
        )}

        {tab === 1 && (
          <Box sx={{ p: 1.5 }}>
            <Stack direction={{ xs: "column", sm: "row" }} sx={{ mb: 1.5, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, gap: 1 }}>
              <Box><Typography sx={{ fontWeight: 800 }}>موجودی بر اساس بچ</Typography><Typography variant="body2" color="text.secondary">اینجا دقیقاً مشخص است هر کالا در کدام بچ چه مقدار موجودی دارد.</Typography></Box>
              <Stack direction="row" spacing={1}>
                <Button variant={batchFilter === "active" ? "contained" : "outlined"} onClick={() => setBatchFilter("active")}>بچ‌های موجود</Button>
                <Button variant={batchFilter === "empty" ? "contained" : "outlined"} onClick={() => setBatchFilter("empty")}>بچ‌های تمام‌شده</Button>
              </Stack>
            </Stack>
            {batchLoading ? <CircularProgress /> : <TableContainer component={Card} variant="outlined">
              <Table size="small">
                <TableHead><TableRow><TableCell>بچ</TableCell><TableCell>کالا</TableCell><TableCell>تاریخ دریافت</TableCell><TableCell>اولیه</TableCell><TableCell>مانده</TableCell><TableCell>قیمت خرید</TableCell><TableCell>قیمت فروش</TableCell><TableCell>وضعیت</TableCell></TableRow></TableHead>
                <TableBody>{batches.map((b) => <TableRow hover key={b.id}>
                  <TableCell sx={{ fontWeight: 800 }}>#{b.id}</TableCell><TableCell sx={{ fontWeight: 700 }}>{b.product_name}</TableCell>
                  <TableCell>{b.received_at}</TableCell><TableCell>{b.quantity}</TableCell><TableCell>{b.remaining_quantity}</TableCell>
                  <TableCell>{money(b.purchase_price)}</TableCell><TableCell>{money(b.sale_price)}</TableCell>
                  <TableCell><Chip size="small" color={Number(b.remaining_quantity) > 0 ? "success" : "default"} label={Number(b.remaining_quantity) > 0 ? "موجود" : "تمام‌شده"} /></TableCell>
                </TableRow>)}
                {!batches.length && <TableRow><TableCell colSpan={8} align="center">بچی با این وضعیت پیدا نشد.</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>}
          </Box>
        )}
      </Paper>

      <Dialog open={!!edit} onClose={() => setEdit(null)} fullWidth maxWidth="sm"><DialogTitle>مدیریت موجودی {edit?.product_name}</DialogTitle><DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField label="حداقل موجودی" type="number" value={min} onChange={(e) => setMin(e.target.value)} /><TextField label="موجودی جدید" type="number" value={qty} onChange={(e) => setQty(e.target.value)} helperText="این مقدار به‌عنوان تعدیل در گردش کالا ثبت می‌شود." /><TextField label="شرح تعدیل" value={desc} onChange={(e) => setDesc(e.target.value)} /></Stack></DialogContent><DialogActions><Button onClick={() => setEdit(null)}>انصراف</Button><Button onClick={() => void saveMin()}>ذخیره حداقل</Button><Button variant="contained" onClick={() => void adjust()}>ثبت تعدیل</Button></DialogActions></Dialog>
      <Dialog open={!!historyTitle} onClose={() => setHistoryTitle("")} fullWidth maxWidth="md"><DialogTitle>گردش {historyTitle}</DialogTitle><DialogContent><Table size="small"><TableHead><TableRow><TableCell>نوع</TableCell><TableCell>مقدار</TableCell><TableCell>شرح</TableCell><TableCell>تاریخ</TableCell></TableRow></TableHead><TableBody>{history.map((t) => <TableRow key={t.id}><TableCell>{t.transaction_type === "sale" ? "فروش" : t.transaction_type === "purchase" ? "خرید" : t.transaction_type === "return" ? "برگشت" : "تعدیل"}</TableCell><TableCell>{t.quantity}</TableCell><TableCell>{t.description || "-"}</TableCell><TableCell>{t.created_at}</TableCell></TableRow>)}</TableBody></Table></DialogContent></Dialog>
    </Box>
  );
}
