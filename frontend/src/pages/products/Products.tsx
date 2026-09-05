import { useEffect, useState } from "react";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";

import {
  Alert,
  Button,
  CircularProgress,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { deleteProduct, listProducts, type Product } from "../../services/productService";
import ProductForm from "./ProductForm";
import { useStore } from "../../contexts/StoreContext";


function Products() {
  const { activeStore } = useStore();	
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] =
    useState<Product | null>(null);
  
	const loadProducts = () => {
	  if (!activeStore) {
		setProducts([]);
		return;
	  }

    setLoading(true);
    setError("");

    void listProducts(activeStore.id)
      .then(setProducts)
      .catch((error) => {
        console.error("PRODUCTS ERROR:", error);
        setError("خطا در دریافت محصولات");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProducts();
  }, [activeStore]);

	const handleDelete = async (product: Product) => {
	  const confirmed = window.confirm(
		`آیا از حذف محصول «${product.name}» مطمئن هستید؟`
	  );

	  if (!confirmed) {
		return;
	  }

	  try {
    await deleteProduct(product.id);

		loadProducts();
  	  } catch (error: any) {
	    console.error(
	   	  "DELETE PRODUCT ERROR:",
		  error.response?.status
	    );

	    console.error(
		  "DELETE PRODUCT DATA:",
		  error.response?.data
	    );

	    if (error.response?.status === 400) {
		  setError(
		    "این محصول دارای سابقه خرید، فروش یا برگشت است و قابل حذف نیست. در صورت نیاز، محصول را غیرفعال کنید."
		  );
	    } else {
		  setError("خطا در حذف محصول");
	    }
	  }
	};
	
  if (showForm) {
    return (
      <Paper
        sx={{
          p: 3,
          direction: "rtl",
        }}
      >
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
    <>
      <Typography
        variant="h4"
        sx={{
          textAlign: "right",
          mb: 3,
        }}
      >
        محصولات
      </Typography>

      <Button
        variant="contained"
        onClick={() => setShowForm(true)}
        sx={{
          mb: 3,
        }}
      >
        + افزودن محصول
      </Button>

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
        <TableContainer
          component={Paper}
          sx={{
            direction: "rtl",
          }}
        >
          <Table
            sx={{
              direction: "rtl",
              "& th, & td": {
                textAlign: "right",
              },
            }}
          >
            <TableHead>
              <TableRow>
				<TableCell align="right">
				  ردیف
				</TableCell>
				
                <TableCell align="right">
                  نام محصول
                </TableCell>

                <TableCell align="right">
                  بارکد
                </TableCell>

                <TableCell align="right">
                  واحد
                </TableCell>

                <TableCell align="right">
                  قیمت خرید
                </TableCell>

                <TableCell align="right">
                  قیمت فروش
                </TableCell>

                <TableCell align="right">
                  وضعیت
                </TableCell>
                <TableCell align="right">
                  عملیات
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {products.map((product, index) => (
                <TableRow key={product.id}>
				  <TableCell align="right">
				    {index + 1}
				  </TableCell>		
				  
                  <TableCell align="right">
                    {product.name}
                  </TableCell>

                  <TableCell align="right">
                    {product.barcode || "-"}
                  </TableCell>

                  <TableCell align="right">
                    {product.unit || "-"}
                  </TableCell>

                  <TableCell align="right">
                    {product.purchase_price || "-"}
                  </TableCell>

                  <TableCell align="right">
                    {product.sale_price || "-"}
                  </TableCell>

                  <TableCell align="right">
                    {product.is_active
                      ? "فعال"
                      : "غیرفعال"}
                  </TableCell>
				  <TableCell align="right">
				    <IconButton
					  color="primary"
					  onClick={() => {
					    setEditingProduct(product);
					    setShowForm(true);
					  }}
				    >
					  <EditIcon />
				    </IconButton>

				    <IconButton
					  color="error"
					  onClick={() => handleDelete(product)}
				    >
					  <DeleteIcon />
				    </IconButton>
				  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </>
  );
}

export default Products;