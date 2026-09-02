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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from "@mui/material";

import api from "../../services/api";
import { useStore } from "../../contexts/StoreContext";

interface PurchaseItem {
  id: number;
  product: number;
  product_name: string;
  quantity: string;
  unit_price: string;
  total_price: string;
}

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
  items: PurchaseItem[];
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

  const [editingPurchase, setEditingPurchase] =
    useState<Purchase | null>(null);

  const [selectedPurchase, setSelectedPurchase] =
    useState<Purchase | null>(null);

  const [deletePurchase, setDeletePurchase] =
    useState<Purchase | null>(null);

  const [deleting, setDeleting] =
    useState(false);
  
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
        editingPurchase={editingPurchase}
        onSuccess={async () => {
          setShowForm(false);
          setEditingPurchase(null);
          await loadPurchases();
        }}
        onCancel={() => {
          setShowForm(false);
          setEditingPurchase(null);
        }}
      />
    );
  }

  const handleCloseDetails = () => {
    setSelectedPurchase(null);
  };

  const handleNewPurchase = () => {
    setEditingPurchase(null);
    setShowForm(true);
  };

  const handleEditPurchase = (purchase: Purchase) => {
    setEditingPurchase(purchase);
    setShowForm(true);
  };

	const handleDeletePurchase = async () => {
	  if (!deletePurchase) {
		return;
	  }

	  setDeleting(true);
	  setError("");

	  try {
		await api.delete(
		  `/products/purchases/${deletePurchase.id}/`
		);

		setDeletePurchase(null);

		await loadPurchases();
	  } catch (error: any) {
		console.error(
		  "DELETE PURCHASE ERROR:",
		  error.response?.status
		);

		console.error(
		  "DELETE PURCHASE DATA:",
		  error.response?.data
		);

		setError(
		  error.response?.data?.detail ||
			"خطا در حذف خرید."
		);
	  } finally {
		setDeleting(false);
	  }
	};

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
          onClick={handleNewPurchase}
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
        <>
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
                  <TableCell>عملیات</TableCell>
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

					  <TableCell>
					    <Box
					  	  sx={{
						    display: "flex",
						    gap: 1,
						  }}
					    >
						  <Button
						    size="small"
						    variant="outlined"
						    onClick={() =>
						  	setSelectedPurchase(purchase)
						    }
						  >
						    جزئیات
					  	  </Button>

						  <Button
						    size="small"
						    variant="outlined"
						    disabled={purchase.received}
						    onClick={() =>
							  handleEditPurchase(purchase)
						    }
						  >
						    ویرایش
						  </Button>

						  <Button
						    size="small"
						    variant="outlined"
						    color="error"
						    disabled={purchase.received}
						    onClick={() =>
						  	setDeletePurchase(purchase)
						    }
						  >
						    حذف
						  </Button>
					    </Box>
					  </TableCell>
                    </TableRow>
                  )
                )}

                {purchases.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={10}
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

          <Dialog
            open={selectedPurchase !== null}
            onClose={handleCloseDetails}
            fullWidth
            maxWidth="md"
            dir="rtl"
          >
            <DialogTitle>
              جزئیات خرید شماره{" "}
              {selectedPurchase?.id}
            </DialogTitle>

            <DialogContent>
              {selectedPurchase && (
                <>
                  <Typography sx={{ mb: 1 }}>
                    فروشگاه:{" "}
                    {selectedPurchase.store_name}
                  </Typography>

                  <Typography sx={{ mb: 1 }}>
                    تأمین‌کننده:{" "}
                    {selectedPurchase.supplier_name}
                  </Typography>

                  <Typography sx={{ mb: 1 }}>
                    فاکتور:{" "}
                    {selectedPurchase.invoice_number || "-"}
                  </Typography>

                  <Typography sx={{ mb: 2 }}>
                    تاریخ:{" "}
                    {selectedPurchase.created_at}
                  </Typography>

                  <Divider sx={{ mb: 2 }} />

                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ردیف</TableCell>
                        <TableCell>محصول</TableCell>
                        <TableCell>تعداد</TableCell>
                        <TableCell>قیمت واحد</TableCell>
                        <TableCell>مبلغ</TableCell>
                      </TableRow>
                    </TableHead>

                    <TableBody>
                      {selectedPurchase.items.map(
                        (item, index) => (
                          <TableRow key={item.id}>
                            <TableCell>
                              {index + 1}
                            </TableCell>

                            <TableCell>
                              {item.product_name}
                            </TableCell>

                            <TableCell>
                              {item.quantity}
                            </TableCell>

                            <TableCell>
                              {Number(
                                item.unit_price
                              ).toLocaleString("fa-IR")}
                            </TableCell>

                            <TableCell>
                              {Number(
                                item.total_price
                              ).toLocaleString("fa-IR")}
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>

                  <Divider sx={{ my: 2 }} />

                  <Typography
                    variant="h6"
                    sx={{ textAlign: "right" }}
                  >
                    مبلغ کل:{" "}
                    {Number(
                      selectedPurchase.total_amount
                    ).toLocaleString("fa-IR")}{" "}
                    تومان
                  </Typography>
                </>
              )}
            </DialogContent>

            <DialogActions>
              <Button
                onClick={handleCloseDetails}
              >
                بستن
              </Button>
            </DialogActions>
          </Dialog>

		  {/* دیالوگ تأیید حذف */}
		  <Dialog
  		    open={deletePurchase !== null}
		    onClose={() => {
			  if (!deleting) {
			    setDeletePurchase(null);
			  }
		    }}
		    dir="rtl"
		  >
 		    <DialogTitle>
			  تأیید حذف خرید
		    </DialogTitle>
 
		    <DialogContent>
			  <Typography>
			    آیا از حذف خرید شماره{" "}
			    <strong>
				  {deletePurchase?.id}
			    </strong>{" "}
			    مطمئن هستید؟
			  </Typography>

			  <Typography
			    sx={{
				  mt: 2,
				  color: "error.main",
			    }}
			  >
			    این عملیات قابل بازگشت نیست.
			  </Typography>
		    </DialogContent>

		    <DialogActions>
			  <Button
			    onClick={() =>
				  setDeletePurchase(null)
			    }
			    disabled={deleting}
			  >
			    انصراف
			  </Button>

			  <Button
  			    color="error"
			    variant="contained"
			    onClick={handleDeletePurchase}
			    disabled={deleting}
			  >
			    {deleting
				  ? "در حال حذف..."
				  : "حذف خرید"}
			  </Button>
		    </DialogActions>
		  </Dialog>		  
		  
        </>
      )}
    </>
  );
}

export default Purchases;