import { useEffect, useState } from "react";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import MoreVertIcon from "@mui/icons-material/MoreVert";

import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Menu,
  MenuItem,
  Paper,
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

import {
  deleteProduct,
  getProductBarcode,
  getProductLabel,
  getProductLabels,
  getProductQRCode,
  listProducts,
  type Product,
} from "../../services/productService";
import ProductForm from "./ProductForm";
import { useStore } from "../../contexts/StoreContext";

type PreviewFile = {
  title: string;
  url: string;
  kind: "image" | "pdf";
};

function Products() {
  const { activeStore } = useStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const [menuProduct, setMenuProduct] = useState<Product | null>(null);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [previewFile, setPreviewFile] = useState<PreviewFile | null>(null);
  const [labelsProduct, setLabelsProduct] = useState<Product | null>(null);
  const [labelCount, setLabelCount] = useState("9");

  const loadProducts = () => {
    if (!activeStore) {
      setProducts([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    void listProducts(activeStore.id)
      .then(setProducts)
      .catch((loadError) => {
        console.error("PRODUCTS ERROR:", loadError);
        setError("خطا در دریافت محصولات");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProducts();
  }, [activeStore]);

  useEffect(() => {
    return () => {
      if (previewFile) {
        URL.revokeObjectURL(previewFile.url);
      }
    };
  }, [previewFile]);

  const handleDelete = async (product: Product) => {
    const confirmed = window.confirm(
      `آیا از حذف محصول «${product.name}» مطمئن هستید؟`,
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteProduct(product.id);
      loadProducts();
    } catch (deleteError: any) {
      console.error("DELETE PRODUCT ERROR:", deleteError.response?.status);
      console.error("DELETE PRODUCT DATA:", deleteError.response?.data);

      if (deleteError.response?.status === 400) {
        setError(
          "این محصول دارای سابقه خرید، فروش یا برگشت است و قابل حذف نیست. در صورت نیاز، محصول را غیرفعال کنید.",
        );
      } else {
        setError("خطا در حذف محصول");
      }
    }
  };

  const closeMenu = () => {
    setMenuAnchor(null);
    setMenuProduct(null);
  };

  const showBlob = (blob: Blob, title: string, kind: "image" | "pdf") => {
    const url = URL.createObjectURL(blob);
    setPreviewFile((current) => {
      if (current) {
        URL.revokeObjectURL(current.url);
      }
      return { title, url, kind };
    });
  };

  const loadDocument = async (
    title: string,
    kind: "image" | "pdf",
    loader: () => Promise<Blob>,
  ) => {
    setDocumentLoading(true);
    setError("");
    try {
      const blob = await loader();
      showBlob(blob, title, kind);
    } catch (documentError: any) {
      console.error("PRODUCT DOCUMENT ERROR:", documentError.response?.status);
      setError("خطا در دریافت فایل محصول.");
    } finally {
      setDocumentLoading(false);
      closeMenu();
    }
  };

  const handleLabels = async () => {
    if (!labelsProduct) {
      return;
    }

    const count = Number(labelCount);
    if (!Number.isInteger(count) || count < 1 || count > 200) {
      setError("تعداد لیبل باید یک عدد صحیح بین ۱ تا ۲۰۰ باشد.");
      return;
    }

    const product = labelsProduct;
    setLabelsProduct(null);
    await loadDocument(
      `لیبل‌های ${product.name}`,
      "pdf",
      () => getProductLabels(product.id, count),
    );
  };

  if (showForm) {
    return (
      <Paper sx={{ p: 3, direction: "rtl" }}>
        <ProductForm
          product={editingProduct}
          onSuccess={() => {
            setShowForm(false);
            setEditingProduct(null);
            loadProducts();
          }}
          onCancel={() => {
            setShowForm(false);
            setEditingProduct(null);
          }}
        />
      </Paper>
    );
  }

  return (
    <Box dir="rtl" className="page-shell">
      <Box className="page-header">
        <Box className="page-header-title">
          <Typography variant="h5" className="soft-title">محصولات</Typography>
        </Box>
        <Box className="page-header-actions">
          <Button variant="contained" onClick={() => setShowForm(true)}>+ افزودن محصول</Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper} sx={{ direction: "rtl" }}>
          <Table sx={{ direction: "rtl", "& th, & td": { textAlign: "right" } }}>
            <TableHead>
              <TableRow>
                <TableCell align="right">ردیف</TableCell>
                <TableCell align="right">نام محصول</TableCell>
                <TableCell align="right">بارکد</TableCell>
                <TableCell align="right">واحد</TableCell>
                <TableCell align="right">قیمت فروش پیش‌فرض</TableCell>
                <TableCell align="right">وضعیت</TableCell>
                <TableCell align="right">عملیات</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {products.map((product, index) => (
                <TableRow key={product.id}>
                  <TableCell align="right">{index + 1}</TableCell>
                  <TableCell align="right">{product.name}</TableCell>
                  <TableCell align="right">{product.barcode || "-"}</TableCell>
                  <TableCell align="right">{product.unit || "-"}</TableCell>
                  <TableCell align="right">
                    {Number(product.effective_sale_price || product.sale_price || 0).toLocaleString("fa-IR")}
                  </TableCell>
                  <TableCell align="right">{product.is_active ? "فعال" : "غیرفعال"}</TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5}>
                      <IconButton
                        color="primary"
                        size="small"
                        onClick={() => {
                          setEditingProduct(product);
                          setShowForm(true);
                        }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>

                      <IconButton color="error" size="small" onClick={() => void handleDelete(product)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>

                      <IconButton
                        size="small"
                        disabled={documentLoading}
                        onClick={(event) => {
                          setMenuAnchor(event.currentTarget);
                          setMenuProduct(product);
                        }}
                      >
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={closeMenu}>
        <MenuItem
          disabled={!menuProduct || documentLoading}
          onClick={() => menuProduct && void loadDocument(
            `بارکد ${menuProduct.name}`,
            "image",
            () => getProductBarcode(menuProduct.id),
          )}
        >
          مشاهده بارکد
        </MenuItem>
        <MenuItem
          disabled={!menuProduct || documentLoading}
          onClick={() => menuProduct && void loadDocument(
            `QR محصول ${menuProduct.name}`,
            "image",
            () => getProductQRCode(menuProduct.id),
          )}
        >
          مشاهده QR Code
        </MenuItem>
        <MenuItem
          disabled={!menuProduct || documentLoading}
          onClick={() => menuProduct && void loadDocument(
            `لیبل ${menuProduct.name}`,
            "pdf",
            () => getProductLabel(menuProduct.id),
          )}
        >
          لیبل تکی
        </MenuItem>
        <MenuItem
          disabled={!menuProduct || documentLoading}
          onClick={() => {
            if (menuProduct) {
              setLabelsProduct(menuProduct);
              setLabelCount("9");
            }
            closeMenu();
          }}
        >
          چاپ چند لیبل
        </MenuItem>
      </Menu>

      <Dialog
        open={previewFile !== null}
        onClose={() => setPreviewFile(null)}
        fullWidth
        maxWidth="md"
        dir="rtl"
      >
        <DialogTitle>{previewFile?.title}</DialogTitle>
        <DialogContent dividers sx={{ minHeight: 420 }}>
          {previewFile?.kind === "image" ? (
            <Box
              component="img"
              src={previewFile.url}
              alt={previewFile.title}
              sx={{ display: "block", maxWidth: "100%", mx: "auto" }}
            />
          ) : previewFile ? (
            <Box
              component="iframe"
              src={previewFile.url}
              title={previewFile.title}
              sx={{ width: "100%", height: 560, border: 0 }}
            />
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button
            variant="outlined"
            onClick={() => {
              if (previewFile) {
                const printWindow = window.open(previewFile.url, "_blank", "noopener,noreferrer");
                printWindow?.focus();
              }
            }}
          >
            باز کردن برای چاپ
          </Button>
          <Button onClick={() => setPreviewFile(null)}>بستن</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={labelsProduct !== null} onClose={() => setLabelsProduct(null)} dir="rtl">
        <DialogTitle>چاپ چند لیبل</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography sx={{ mb: 2 }}>
            محصول: <strong>{labelsProduct?.name}</strong>
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="تعداد لیبل"
            type="number"
            value={labelCount}
            onChange={(event) => setLabelCount(event.target.value)}
            slotProps={{ htmlInput: { min: 1, max: 200, step: 1 } }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLabelsProduct(null)}>انصراف</Button>
          <Button variant="contained" disabled={documentLoading} onClick={() => void handleLabels()}>
            ایجاد فایل
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Products;
