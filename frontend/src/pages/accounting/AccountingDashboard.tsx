import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import SyncIcon from "@mui/icons-material/Sync";
import SettingsIcon from "@mui/icons-material/Settings";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import SavingsIcon from "@mui/icons-material/Savings";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../contexts/StoreContext";
import { getBalanceSheet, getProfitLoss, getTrialBalance, setupAccounting, syncAccounting } from "../../services/accountingService";
import { getApiErrorMessage } from "../../utils/apiError";
import { money } from "./accountingUtils";

export default function AccountingDashboard() {
  const { activeStore } = useStore();
  const navigate = useNavigate();
  const [profit, setProfit] = useState<{ revenue: string | number; expense: string | number; net_profit: string | number } | null>(null);
  const [sheet, setSheet] = useState<{ assets: string | number; liabilities: string | number; equity: string | number; balanced: boolean } | null>(null);
  const [entryCount, setEntryCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<"setup" | "sync" | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    if (!activeStore) return;
    setLoading(true);
    setError("");
    try {
      const [p, b, tb] = await Promise.all([
        getProfitLoss({ store: activeStore.id }),
        getBalanceSheet(activeStore.id),
        getTrialBalance({ store: activeStore.id }),
      ]);
      setProfit(p);
      setSheet(b);
      setEntryCount(tb.length);
    } catch (e) {
      setError(getApiErrorMessage(e, "بارگذاری داشبورد حسابداری انجام نشد."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [activeStore?.id]);

  const run = async (type: "setup" | "sync") => {
    if (!activeStore) return;
    setBusy(type);
    setError("");
    setMessage("");
    try {
      if (type === "setup") await setupAccounting(activeStore.id);
      else await syncAccounting(activeStore.id);
      setMessage(type === "setup" ? "ساختار حسابداری فروشگاه آماده شد." : "اطلاعات حسابداری با سوابق فروشگاه همگام‌سازی شد.");
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "عملیات حسابداری انجام نشد."));
    } finally {
      setBusy(null);
    }
  };

  if (!activeStore) return <Alert severity="warning">ابتدا یک فروشگاه انتخاب کنید.</Alert>;

  return (
    <Box dir="rtl">
      <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 1, mb: 2 }}>
        <Box>
          <Typography variant="h5">داشبورد حسابداری</Typography>
          <Typography color="text.secondary">فروشگاه: {activeStore.name}</Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button startIcon={<RefreshIcon />} variant="outlined" onClick={() => void load()} disabled={loading}>به‌روزرسانی</Button>
          <Button startIcon={<SettingsIcon />} variant="contained" onClick={() => void run("setup")} disabled={busy !== null}>{busy === "setup" ? "در حال آماده‌سازی..." : "آماده‌سازی"}</Button>
          <Button startIcon={<SyncIcon />} variant="contained" color="secondary" onClick={() => void run("sync")} disabled={busy !== null}>{busy === "sync" ? "در حال همگام‌سازی..." : "همگام‌سازی"}</Button>
        </Stack>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}

      {loading && !profit ? (
        <Box sx={{ py: 8, display: "grid", placeItems: "center" }}><CircularProgress /></Box>
      ) : (
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
          <Box>
            <Card><CardContent><Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}><TrendingUpIcon color="primary" /><Box><Typography color="text.secondary">درآمد</Typography><Typography variant="h6">{money(profit?.revenue)}</Typography></Box></Box></CardContent></Card>
          </Box>
          <Box>
            <Card><CardContent><Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}><SavingsIcon color="error" /><Box><Typography color="text.secondary">هزینه</Typography><Typography variant="h6">{money(profit?.expense)}</Typography></Box></Box></CardContent></Card>
          </Box>
          <Box>
            <Card><CardContent><Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}><AccountBalanceIcon color="success" /><Box><Typography color="text.secondary">سود خالص</Typography><Typography variant="h6">{money(profit?.net_profit)}</Typography></Box></Box></CardContent></Card>
          </Box>
          <Box>
            <Card><CardContent><Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}><AccountBalanceIcon color="secondary" /><Box><Typography color="text.secondary">دارایی‌ها</Typography><Typography variant="h6">{money(sheet?.assets)}</Typography></Box></Box></CardContent></Card>
          </Box>

          <Box sx={{ gridColumn: { xs: "auto", md: "span 2" } }}>
            <Card><CardContent><Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 1 }}><Typography variant="h6">وضعیت ترازنامه</Typography><Chip label={sheet?.balanced ? "متوازن" : "نامتوازن"} color={sheet?.balanced ? "success" : "error"} size="small" /></Stack><Typography color="text.secondary">بدهی‌ها: {money(sheet?.liabilities)}</Typography><Typography color="text.secondary">حقوق مالکانه: {money(sheet?.equity)}</Typography></CardContent></Card>
          </Box>
          <Box sx={{ gridColumn: { xs: "auto", md: "span 2" } }}>
            <Card><CardContent><Typography variant="h6" sx={{ mb: 1 }}>دسترسی سریع</Typography><Stack direction={{ xs: "column", sm: "row" }} spacing={1}><Button variant="outlined" onClick={() => navigate("/accounting/accounts")}>سرفصل حساب‌ها</Button><Button variant="outlined" onClick={() => navigate("/accounting/periods")}>دوره‌های مالی</Button><Button variant="outlined" onClick={() => navigate("/accounting/entries")}>اسناد حسابداری</Button><Button variant="outlined" onClick={() => navigate("/accounting/reports")}>گزارش‌ها</Button></Stack><Typography color="text.secondary" sx={{ mt: 1 }}>تعداد ردیف‌های فعال در تراز آزمایشی: {new Intl.NumberFormat("fa-IR").format(entryCount)}</Typography></CardContent></Card>
          </Box>
        </Box>
      )}
    </Box>
  );
}
