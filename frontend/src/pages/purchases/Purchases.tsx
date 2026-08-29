import { useEffect, useState } from "react";
import PurchaseForm from "./PurchaseForm";

import {
  Alert,
  Box,
  Button,
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

import api from "../../services/api";
import { useStore } from "../../contexts/StoreContext";

interface Purchase {
  id: number;
  supplier: number;
  supplier_name: string;
  store: number;
  store_name: string;
  user: number;
  invoice_number: string;
  total_amount: string;
  created_at: string;
  received: boolean;
  username: string;
  item_count: number;
}

function Purchases() {
  const {
    activeStore,
    loading: storeLoading,
  } = useStore();

  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);  

	  const loadPurchases = async () => {
	  if (!activeStore) {
		setPurchases([]);
		return;
	  }

	  setLoading(true);
	  setError("");

	  try {
		const response = await api.get(
		  "/products/purchases/",
		  {
			params: {
			  store: activeStore.id,
			},
		  }
		);

		const data = Array.isArray(response.data)
		  ? response.data
		  : response.data.results;

		setPurchases(data || []);
	  } catch (error: any) {
		console.error(
		  "PURCHASES ERROR:",
		  error.response?.status
		);

		console.error(
		  "PURCHASES DATA:",
		  error.response?.data
		);

		setError(
		  "خطا در دریافت لیست خریدها."
		);
	  } finally {
		setLoading(false);
	  }
	};

	useEffect(() => {
	  loadPurchases();
	}, [activeStore]);

  if (storeLoading) {
    return (
      <Typography>
        در حال دریافت فروشگاه...
      </Typography>
    );
  }

  if (!activeStore) {
    return (
      <Alert severity="warning">
        فروشگاه فعالی انتخاب نشده است.
      </Alert>
    );
  }

	if (showForm) {
	  return (
		<PurchaseForm
			onSuccess={async () => {
			  setShowForm(false);
			  await loadPurchases();
			}}
		  onCancel={() => {
			setShowForm(false);
		  }}
		/>
	  );
	}

  return (
    <>
		<Box
		  sx={{
			display: "flex",
			flexDirection: "row-reverse",
			alignItems: "center",
			justifyContent: "space-between",
			mb: 3,
		  }}
		>
		  <Typography variant="h5">
			خریدهای {activeStore.name}
		  </Typography>

		  <Button
			variant="contained"
			onClick={() => setShowForm(true)}
		  >
			ثبت خرید جدید
		  </Button>
		</Box>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ردیف</TableCell>
                <TableCell>شماره خرید</TableCell>
                <TableCell>تأمین‌کننده</TableCell>
                <TableCell>فاکتور</TableCell>
                <TableCell>مبلغ کل</TableCell>
                <TableCell>تعداد اقلام</TableCell>
                <TableCell>وضعیت</TableCell>
                <TableCell>ثبت‌کننده</TableCell>
                <TableCell>تاریخ</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {purchases.map(
                (purchase, index) => (
                  <TableRow
                    key={purchase.id}
                  >
                    <TableCell>
                      {index + 1}
                    </TableCell>

                    <TableCell>
                      {purchase.id}
                    </TableCell>

                    <TableCell>
                      {purchase.supplier_name}
                    </TableCell>

                    <TableCell>
                      {purchase.invoice_number || "-"}
                    </TableCell>

                    <TableCell>
                      {Number(
                        purchase.total_amount
                      ).toLocaleString("fa-IR")}
                    </TableCell>

                    <TableCell>
                      {purchase.item_count}
                    </TableCell>

                    <TableCell>
                      {purchase.received
                        ? "دریافت شده"
                        : "دریافت نشده"}
                    </TableCell>

                    <TableCell>
                      {purchase.username}
                    </TableCell>

                    <TableCell>
                      {purchase.created_at}
                    </TableCell>
                  </TableRow>
                )
              )}

              {purchases.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={9}
                    align="center"
                  >
                    خریدی برای این فروشگاه
                    ثبت نشده است.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </>
  );
}

export default Purchases;