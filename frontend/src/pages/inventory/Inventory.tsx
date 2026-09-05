import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { listInventory, type InventoryItem } from "../../services/inventoryService";
import { useStore } from "../../contexts/StoreContext";

function Inventory() {
  const { activeStore } = useStore();
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!activeStore) {
      setItems([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    void listInventory(activeStore.id)
      .then(setItems)
      .catch((requestError) => {
        console.error("INVENTORY ERROR:", requestError);
        setError("خطا در دریافت موجودی کالاها");
      })
      .finally(() => setLoading(false));
  }, [activeStore]);

  const lowStockCount = useMemo(
    () => items.filter((item) => Number(item.quantity) <= Number(item.min_quantity)).length,
    [items],
  );

  return (
    <div dir="rtl">
      <Typography variant="h5" sx={{ mb: 2 }}>
        موجودی کالاها
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!loading && items.length > 0 && (
        <Alert severity={lowStockCount > 0 ? "warning" : "success"} sx={{ mb: 2 }}>
          {lowStockCount > 0
            ? `${lowStockCount} کالا در حداقل موجودی یا پایین‌تر قرار دارد.`
            : "موجودی کالاها در محدوده حداقل تعیین‌شده قرار دارد."}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell align="right">ردیف</TableCell>
                <TableCell align="right">کالا</TableCell>
                <TableCell align="right">بارکد</TableCell>
                <TableCell align="right">موجودی</TableCell>
                <TableCell align="right">حداقل موجودی</TableCell>
                <TableCell align="right">وضعیت</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item, index) => {
                const lowStock = Number(item.quantity) <= Number(item.min_quantity);
                return (
                  <TableRow key={item.id}>
                    <TableCell align="right">{index + 1}</TableCell>
                    <TableCell align="right">{item.product_name}</TableCell>
                    <TableCell align="right">{item.barcode || "-"}</TableCell>
                    <TableCell align="right">{item.quantity}</TableCell>
                    <TableCell align="right">{item.min_quantity}</TableCell>
                    <TableCell align="right">{lowStock ? "نیازمند تأمین" : "مناسب"}</TableCell>
                  </TableRow>
                );
              })}
              {items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    موجودی‌ای برای این فروشگاه ثبت نشده است.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </div>
  );
}

export default Inventory;
