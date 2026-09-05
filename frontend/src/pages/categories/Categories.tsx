import { useEffect, useState } from "react";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import CategoryForm from "./CategoryForm";
import { useStore } from "../../contexts/StoreContext";
import { deleteCategory, listCategories } from "../../services/categoryService";

import {
  Alert,
  Box,
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

interface Category {
  id: number;
  name: string;
  store: number;
  store_name?: string;
  is_active?: boolean;
  created_at?: string;
}

function Categories() {
  const {
    activeStore,
    loading: storeLoading,
  } = useStore();

  const [categories, setCategories] =
    useState<Category[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [showForm, setShowForm] =
    useState(false);

  const loadCategories = async () => {
    if (!activeStore) {
      setCategories([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await listCategories(activeStore.id);
      setCategories(data);

    } catch (error: any) {

      console.error(
        "CATEGORIES ERROR:",
        error.response?.status
      );

      console.error(
        "CATEGORIES DATA:",
        error.response?.data
      );

      setError(
        "خطا در دریافت دسته‌بندی‌ها"
      );

    } finally {

      setLoading(false);

    }
  };

  useEffect(() => {
    loadCategories();
  }, [activeStore]);


  const handleDelete = async (
    category: Category
  ) => {

    const confirmed =
      window.confirm(
        `آیا از حذف دسته‌بندی «${category.name}» مطمئن هستید؟`
      );

    if (!confirmed) {
      return;
    }

    setError("");

    try {

      if (!activeStore) {
        setError("فروشگاه فعالی انتخاب نشده است.");
        return;
      }

      await deleteCategory(category.id, activeStore.id);

      await loadCategories();

    } catch (error: any) {

      console.error(
        "DELETE CATEGORY ERROR:",
        error.response?.status
      );

      console.error(
        "DELETE CATEGORY DATA:",
        error.response?.data
      );

      if (
        error.response?.status === 400
      ) {

        const responseData =
          error.response?.data;

        if (
          Array.isArray(responseData)
        ) {

          setError(
            responseData[0]
          );

        } else if (
          responseData?.detail
        ) {

          setError(
            responseData.detail
          );

        } else {

          setError(
            "این دسته‌بندی دارای محصول است و قابل حذف نیست."
          );
        }

      } else {

        setError(
          "خطا در حذف دسته‌بندی"
        );

      }
    }
  };


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
      <CategoryForm
        onSuccess={async () => {
          setShowForm(false);
          await loadCategories();
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
          direction: "rtl",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}
      >
        <Button
          variant="contained"
          onClick={() =>
            setShowForm(true)
          }
        >
          + افزودن دسته‌بندی
        </Button>

        <Typography variant="h4">
          دسته‌بندی‌های{" "}
          {activeStore.name}
        </Typography>
      </Box>


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

                <TableCell>
                  ردیف
                </TableCell>

                <TableCell>
                  نام دسته‌بندی
                </TableCell>

                <TableCell>
                  وضعیت
                </TableCell>

                <TableCell>
                  تاریخ ایجاد
                </TableCell>

                <TableCell>
                  عملیات
                </TableCell>

              </TableRow>
            </TableHead>


            <TableBody>

              {categories.map(
                (
                  category,
                  index
                ) => (
                  <TableRow
                    key={category.id}
                  >

                    <TableCell>
                      {index + 1}
                    </TableCell>


                    <TableCell>
                      {category.name}
                    </TableCell>


                    <TableCell>
                      {category.is_active
                        ? "فعال"
                        : "غیرفعال"}
                    </TableCell>


                    <TableCell>
                      {category.created_at ||
                        "-"}
                    </TableCell>


                    <TableCell>

                      <IconButton
                        color="primary"
                        disabled
                      >
                        <EditIcon />
                      </IconButton>


                      <IconButton
                        color="error"
                        onClick={() =>
                          handleDelete(
                            category
                          )
                        }
                      >
                        <DeleteIcon />
                      </IconButton>

                    </TableCell>

                  </TableRow>
                )
              )}


              {categories.length === 0 && (
                <TableRow>

                  <TableCell
                    colSpan={5}
                    align="center"
                  >
                    برای این فروشگاه
                    دسته‌بندی ثبت نشده است.
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

export default Categories;