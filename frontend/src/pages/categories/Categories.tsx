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

import api from "../../services/api";

interface Category {
  id: number;
  name: string;
  store: number;
  store_name?: string;
  is_active?: boolean;
  created_at?: string;
}

function Categories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCategories = () => {
    setLoading(true);
    setError("");

    api
      .get("/products/categories/")
      .then((response) => {
        console.log("CATEGORIES:", response.data);

        const data = Array.isArray(response.data)
          ? response.data
          : response.data.results;

        setCategories(data || []);
      })
      .catch((error) => {
        console.error(
          "CATEGORIES ERROR:",
          error.response?.status
        );

        console.error(
          "CATEGORIES DATA:",
          error.response?.data
        );

        setError("خطا در دریافت دسته‌بندی‌ها");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleDelete = async (category: Category) => {
    const confirmed = window.confirm(
      `آیا از حذف دسته‌بندی «${category.name}» مطمئن هستید؟`
    );

    if (!confirmed) {
      return;
    }

    try {
      await api.delete(
        `/products/categories/${category.id}/`
      );

      loadCategories();
    } catch (error: any) {
      console.error(
        "DELETE CATEGORY ERROR:",
        error.response?.status
      );

      console.error(
        "DELETE CATEGORY DATA:",
        error.response?.data
      );

      if (error.response?.status === 400) {
        const responseData = error.response?.data;

        if (Array.isArray(responseData)) {
          setError(responseData[0]);
        } else if (responseData?.detail) {
          setError(responseData.detail);
        } else {
          setError(
            "این دسته‌بندی دارای محصول است و قابل حذف نیست."
          );
        }
      } else {
        setError("خطا در حذف دسته‌بندی");
      }
    }
  };

  return (
    <>
      <Typography
        variant="h4"
        sx={{
          textAlign: "right",
          mb: 3,
        }}
      >
        دسته‌بندی‌ها
      </Typography>

      <Button
        variant="contained"
        sx={{
          mb: 3,
        }}
      >
        + افزودن دسته‌بندی
      </Button>

      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 2,
            direction: "rtl",
          }}
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
                  نام دسته‌بندی
                </TableCell>

                <TableCell align="right">
                  فروشگاه
                </TableCell>

                <TableCell align="right">
                  وضعیت
                </TableCell>

                <TableCell align="right">
                  تاریخ ایجاد
                </TableCell>

                <TableCell align="right">
                  عملیات
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {categories.map((category) => (
                <TableRow key={category.id}>
                  <TableCell align="right">
                    {category.name}
                  </TableCell>

                  <TableCell align="right">
                    {category.store_name || "-"}
                  </TableCell>

                  <TableCell align="right">
                    {category.is_active
                      ? "فعال"
                      : "غیرفعال"}
                  </TableCell>

                  <TableCell align="right">
                    {category.created_at || "-"}
                  </TableCell>

                  <TableCell align="right">
                    <IconButton
                      color="primary"
                      disabled
                    >
                      <EditIcon />
                    </IconButton>

                    <IconButton
                      color="error"
                      onClick={() =>
                        handleDelete(category)
                      }
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

export default Categories;
