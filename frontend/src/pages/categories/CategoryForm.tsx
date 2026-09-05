import { useState } from "react";

import {
  Alert,
  Button,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { createCategory } from "../../services/categoryService";
import { useStore } from "../../contexts/StoreContext";

interface CategoryFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

function CategoryForm({
  onSuccess,
  onCancel,
}: CategoryFormProps) {
  const { activeStore } = useStore();

  const [name, setName] = useState("");
  const [loading, setLoading] =
    useState(false);
  const [error, setError] =
    useState("");

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

    if (!name.trim()) {
      setError(
        "نام دسته‌بندی را وارد کنید."
      );
      return;
    }

    setLoading(true);

    try {
      await createCategory({
        name: name.trim(),
        store: activeStore.id,
      });

      onSuccess();

    } catch (error: any) {
      console.error(
        "CREATE CATEGORY ERROR:",
        error.response?.status
      );

      console.error(
        "CREATE CATEGORY DATA:",
        error.response?.data
      );

      setError(
        error.response?.data
          ? JSON.stringify(
              error.response.data
            )
          : "خطا در ثبت دسته‌بندی."
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
        maxWidth: 600,
      }}
    >
      <Typography variant="h5">
        ثبت دسته‌بندی جدید
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

      <TextField
        label="نام دسته‌بندی"
        value={name}
        onChange={(event) =>
          setName(event.target.value)
        }
        required
        fullWidth
        autoFocus
      />

      <Stack
        direction="row"
        spacing={2}
      >
        <Button
          type="submit"
          variant="contained"
          disabled={loading}
        >
          {loading
            ? "در حال ثبت..."
            : "ثبت دسته‌بندی"}
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

export default CategoryForm;