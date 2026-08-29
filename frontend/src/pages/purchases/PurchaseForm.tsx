import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import DeleteIcon from "@mui/icons-material/Delete";

import api from "../../services/api";
import { useStore } from "../../contexts/StoreContext";

interface Supplier {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  purchase_price?: string;
  sale_price?: string;
}

interface PurchaseItem {
  product: number | "";
  quantity: string;
  unit_price: string;
}

interface PurchaseFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

function PurchaseForm({
  onSuccess,
  onCancel,
}: PurchaseFormProps) {

  const { activeStore } = useStore();

  const [suppliers, setSuppliers] =
    useState<Supplier[]>([]);

  const [products, setProducts] =
    useState<Product[]>([]);

  const [supplier, setSupplier] =
    useState<number | "">("");

  const [invoiceNumber, setInvoiceNumber] =
    useState("");

  const [received, setReceived] =
    useState(false);

  const [items, setItems] =
    useState<PurchaseItem[]>([
      {
        product: "",
        quantity: "1",
        unit_price: "0",
      },
    ]);

  const [loading, setLoading] =
    useState(false);

  const [dataLoading, setDataLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  // دریافت تأمین‌کنندگان و محصولات فروشگاه فعال
  useEffect(() => {

    if (!activeStore) {
      setSuppliers([]);
      setProducts([]);
      return;
    }

    setDataLoading(true);
    setError("");

    Promise.all([
      api.get("/products/suppliers/", {
        params: {
          store: activeStore.id,
        },
      }),

      api.get("/products/products/", {
        params: {
          store: activeStore.id,
        },
      }),
    ])

      .then(
        ([
          supplierResponse,
          productResponse,
        ]) => {

          const supplierData =
            Array.isArray(
              supplierResponse.data
            )
              ? supplierResponse.data
              : supplierResponse.data.results;

          const productData =
            Array.isArray(
              productResponse.data
            )
              ? productResponse.data
              : productResponse.data.results;

          setSuppliers(
            supplierData || []
          );

          setProducts(
            productData || []
          );
        }
      )

      .catch((error) => {

        console.error(
          "PURCHASE FORM DATA ERROR:",
          error.response?.status
        );

        console.error(
          "PURCHASE FORM DATA:",
          error.response?.data
        );

        setError(
          "خطا در دریافت اطلاعات."
        );
      })

      .finally(() => {
        setDataLoading(false);
      });

  }, [activeStore]);


  // افزودن ردیف جدید
  const handleAddItem = () => {

    setItems([
      ...items,
      {
        product: "",
        quantity: "1",
        unit_price: "0",
      },
    ]);
  };


  // حذف ردیف
  const handleRemoveItem = (
    index: number
  ) => {

    if (items.length === 1) {
      return;
    }

    setItems(
      items.filter(
        (_, itemIndex) =>
          itemIndex !== index
      )
    );
  };


  // تغییر محصول
  const handleProductChange = (
    index: number,
    productId: number
  ) => {

    const selectedProduct =
      products.find(
        (product) =>
          product.id === productId
      );

    const newItems = [...items];

    newItems[index] = {
      ...newItems[index],
      product: productId,
      unit_price:
        selectedProduct?.purchase_price ||
        "0",
    };

    setItems(newItems);
  };


  // تغییر تعداد
  const handleQuantityChange = (
    index: number,
    value: string
  ) => {

    const newItems = [...items];

    newItems[index] = {
      ...newItems[index],
      quantity: value,
    };

    setItems(newItems);
  };


  // تغییر قیمت
  const handlePriceChange = (
    index: number,
    value: string
  ) => {

    const newItems = [...items];

    newItems[index] = {
      ...newItems[index],
      unit_price: value,
    };

    setItems(newItems);
  };


  // مبلغ کل
  const totalAmount = items.reduce(
    (total, item) => {

      const quantity =
        Number(item.quantity) || 0;

      const price =
        Number(item.unit_price) || 0;

      return total + quantity * price;

    },
    0
  );


  // ثبت خرید
  const handleSubmit = async (
    event: React.FormEvent
  ) => {

    event.preventDefault();

    setError("");

    if (!activeStore) {
      setError(
        "فروشگاه فعالی انتخاب نشده است."
      );
      return;
    }

    if (supplier === "") {
      setError(
        "تأمین‌کننده را انتخاب کنید."
      );
      return;
    }

    if (items.length === 0) {
      setError(
        "حداقل یک قلم کالا اضافه کنید."
      );
      return;
    }

    for (const item of items) {

      if (item.product === "") {
        setError(
          "برای تمام ردیف‌ها محصول انتخاب کنید."
        );
        return;
      }

      if (Number(item.quantity) <= 0) {
        setError(
          "تعداد باید بیشتر از صفر باشد."
        );
        return;
      }

      if (Number(item.unit_price) < 0) {
        setError(
          "قیمت نمی‌تواند منفی باشد."
        );
        return;
      }
    }

    setLoading(true);

    try {

      // ایجاد خرید اصلی
      const purchaseResponse =
        await api.post(
          "/products/purchases/",
          {
            supplier,
            store: activeStore.id,
            invoice_number:
              invoiceNumber.trim(),
            received,
          }
        );

      const purchaseId =
        purchaseResponse.data.id;


      // ایجاد تمام اقلام خرید
      for (const item of items) {

        await api.post(
          `/products/purchases/${purchaseId}/items/`,
          {
            product: item.product,
            quantity: item.quantity,
            unit_price: item.unit_price,
          }
        );
      }

      onSuccess();

    } catch (error: any) {

      console.error(
        "CREATE PURCHASE ERROR:",
        error.response?.status
      );

      console.error(
        "CREATE PURCHASE DATA:",
        error.response?.data
      );

      setError(
        error.response?.data
          ? JSON.stringify(
              error.response.data
            )
          : "خطا در ثبت خرید."
      );

    } finally {

      setLoading(false);
    }
  };


  if (!activeStore) {

    return (
      <Alert severity="warning">
        ابتدا یک فروشگاه فعال انتخاب کنید.
      </Alert>
    );
  }


  return (
    <Stack
      component="form"
      onSubmit={handleSubmit}
      spacing={3}
      sx={{
        direction: "rtl",
      }}
    >

      <Typography variant="h5">
        ثبت خرید جدید
      </Typography>


      <Typography variant="body1">
        فروشگاه فعال:{" "}
        <strong>
          {activeStore.name}
        </strong>
      </Typography>


      {error && (
        <Alert severity="error">
          {error}
        </Alert>
      )}


      {/* تأمین‌کننده */}

      <FormControl
        fullWidth
        required
      >

        <InputLabel>
          تأمین‌کننده
        </InputLabel>

        <Select
          value={supplier}
          label="تأمین‌کننده"
          onChange={(event) =>
            setSupplier(
              Number(event.target.value)
            )
          }
          disabled={dataLoading}
        >

          {suppliers.map(
            (item) => (
              <MenuItem
                key={item.id}
                value={item.id}
              >
                {item.name}
              </MenuItem>
            )
          )}

        </Select>

      </FormControl>


      {/* شماره فاکتور */}

      <TextField
        label="شماره فاکتور"
        value={invoiceNumber}
        onChange={(event) =>
          setInvoiceNumber(
            event.target.value
          )
        }
        fullWidth
      />


      {/* اقلام خرید */}

      <Box>

        <Typography
          variant="h6"
          sx={{ mb: 2 }}
        >
          اقلام خرید
        </Typography>


        <TableContainer
          component={Paper}
        >

          <Table>

            <TableHead>

              <TableRow>

                <TableCell>
                  ردیف
                </TableCell>

                <TableCell>
                  محصول
                </TableCell>

                <TableCell>
                  تعداد
                </TableCell>

                <TableCell>
                  قیمت واحد
                </TableCell>

                <TableCell>
                  مبلغ
                </TableCell>

                <TableCell>
                  حذف
                </TableCell>

              </TableRow>

            </TableHead>


            <TableBody>

              {items.map(
                (item, index) => {

                  const rowTotal =
                    (Number(
                      item.quantity
                    ) || 0) *
                    (Number(
                      item.unit_price
                    ) || 0);

                  return (
                    <TableRow
                      key={index}
                    >

                      <TableCell>
                        {index + 1}
                      </TableCell>


                      <TableCell
                        sx={{
                          minWidth: 220,
                        }}
                      >

                        <FormControl
                          fullWidth
                          size="small"
                        >

                          <Select
                            value={
                              item.product
                            }
                            displayEmpty
                            onChange={(
                              event
                            ) =>
                              handleProductChange(
                                index,
                                Number(
                                  event.target.value
                                )
                              )
                            }
                          >

                            <MenuItem
                              value=""
                            >
                              انتخاب محصول
                            </MenuItem>

                            {products.map(
                              (product) => (
                                <MenuItem
                                  key={
                                    product.id
                                  }
                                  value={
                                    product.id
                                  }
                                >
                                  {product.name}
                                </MenuItem>
                              )
                            )}

                          </Select>

                        </FormControl>

                      </TableCell>


                      <TableCell>

                        <TextField
                          size="small"
                          type="number"
                          value={
                            item.quantity
                          }
                          onChange={(
                            event
                          ) =>
                            handleQuantityChange(
                              index,
                              event.target.value
                            )
                          }
                          sx={{
                            width: 100,
                          }}
                        />

                      </TableCell>


                      <TableCell>

                        <TextField
                          size="small"
                          type="number"
                          value={
                            item.unit_price
                          }
                          onChange={(
                            event
                          ) =>
                            handlePriceChange(
                              index,
                              event.target.value
                            )
                          }
                          sx={{
                            width: 140,
                          }}
                        />

                      </TableCell>


                      <TableCell>

                        {rowTotal.toLocaleString(
                          "fa-IR"
                        )}

                      </TableCell>


                      <TableCell>

                        <IconButton
                          color="error"
                          onClick={() =>
                            handleRemoveItem(
                              index
                            )
                          }
                          disabled={
                            items.length === 1
                          }
                        >

                          <DeleteIcon />

                        </IconButton>

                      </TableCell>

                    </TableRow>
                  );
                }
              )}

            </TableBody>

          </Table>

        </TableContainer>


        <Button
          variant="outlined"
          sx={{
            mt: 2,
            alignSelf: "flex-start",
          }}
          onClick={
            handleAddItem
          }
        >
          + افزودن قلم
        </Button>

      </Box>


      {/* مبلغ کل */}

      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
        }}
      >

        <Typography
          variant="h6"
        >
          مبلغ کل:{" "}
          {totalAmount.toLocaleString(
            "fa-IR"
          )}{" "}
          تومان
        </Typography>

      </Box>


      {/* وضعیت دریافت */}

      <Button
        variant={
          received
            ? "contained"
            : "outlined"
        }
        onClick={() =>
          setReceived(!received)
        }
      >
        {received
          ? "خرید دریافت شده است"
          : "خرید دریافت نشده است"}
      </Button>


      {/* دکمه‌ها */}

      <Stack
        direction="row"
        spacing={2}
        sx={{
          justifyContent: "flex-start",
        }}
      >

        <Button
          type="submit"
          variant="contained"
          disabled={
            loading ||
            dataLoading
          }
        >
          {loading
            ? "در حال ثبت..."
            : "ثبت خرید"}
        </Button>


        <Button
          type="button"
          variant="outlined"
          onClick={onCancel}
          disabled={loading}
        >
          انصراف
        </Button>

      </Stack>

    </Stack>
  );
}

export default PurchaseForm;