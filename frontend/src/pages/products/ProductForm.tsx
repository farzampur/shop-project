import { useEffect, useState } from "react";
import { useStore } from "../../contexts/StoreContext";

import {
  Alert,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
  FormControlLabel,
} from "@mui/material";

import { listCategories, type Category } from "../../services/categoryService";
import { createProduct, updateProduct } from "../../services/productService";

interface Product {
  id: number;
  name: string;
  barcode?: string;
  category: number;
  unit?: string;
  purchase_price?: string;
  sale_price?: string;
  is_active?: boolean;
}

interface ProductFormProps {
  product?: Product | null;
  onSuccess: () => void;
  onCancel: () => void;
}

function ProductForm({
  product,
  onSuccess,
  onCancel,
}: ProductFormProps) {
  const { activeStore } = useStore();	
  const isEditMode = Boolean(product);

  const [categories, setCategories] = useState<Category[]>([]);

  const [name, setName] = useState(product?.name || "");
  const [barcode, setBarcode] = useState(product?.barcode || "");
  const [category, setCategory] = useState<number | "">(
    product?.category ?? ""
  );
  const [unit, setUnit] = useState(product?.unit || "عدد");
  const [purchasePrice, setPurchasePrice] = useState(
    product?.purchase_price || "0"
  );
  const [salePrice, setSalePrice] = useState(
    product?.sale_price || "0"
  );
  const [isActive, setIsActive] = useState(
    product?.is_active ?? true
  );

  const [loading, setLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [error, setError] = useState("");


	useEffect(() => {
	  if (!activeStore) {
		setCategories([]);
		setCategoriesLoading(false);
		return;
	  }

	  setCategoriesLoading(true);

    void listCategories(activeStore.id)
      .then(setCategories)
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
		  setCategoriesLoading(false);
		});
	}, [activeStore]);
	

  const handleSubmit = async (
    event: React.FormEvent
  ) => {
    event.preventDefault();

    setError("");

    if (!name.trim()) {
      setError("نام محصول را وارد کنید.");
      return;
    }

    if (category === "") {
      setError("دسته‌بندی را انتخاب کنید.");
      return;
    }
    if (!activeStore) {
      setError("فروشگاه فعالی انتخاب نشده است.");
      return;
    }
    setLoading(true);

    try {
      const data: {
        name: string;
        category: number;
        unit: string;
        purchase_price: string;
        sale_price: string;
        is_active: boolean;
        barcode?: string;
      } = {
        name: name.trim(),
        category,
        unit: unit.trim() || "عدد",
        purchase_price: purchasePrice || "0",
        sale_price: salePrice || "0",
        is_active: isActive,
      };

      if (barcode.trim()) {
        data.barcode = barcode.trim();
      }

      if (isEditMode && product) {
        await updateProduct(product.id, activeStore.id, data);
      } else {
        await createProduct(activeStore.id, data);
      }

      onSuccess();
    } catch (error: any) {
      console.error(
        isEditMode
          ? "UPDATE PRODUCT ERROR:"
          : "CREATE PRODUCT ERROR:",
        error.response?.status
      );

      console.error(
        isEditMode
          ? "UPDATE PRODUCT DATA:"
          : "CREATE PRODUCT DATA:",
        error.response?.data
      );

      setError(
        error.response?.data
          ? JSON.stringify(error.response.data)
          : isEditMode
            ? "خطا در ویرایش محصول"
            : "خطا در ثبت محصول"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack
      component="form"
      onSubmit={handleSubmit}
      spacing={2}
      sx={{
        direction: "rtl",
      }}
    >
      <Typography variant="h5">
        {isEditMode
          ? "ویرایش محصول"
          : "افزودن محصول"}
      </Typography>

      {error && (
        <Alert severity="error">
          {error}
        </Alert>
      )}

      <TextField
        label="نام محصول"
        value={name}
        onChange={(event) =>
          setName(event.target.value)
        }
        fullWidth
        required
      />

      <TextField
        label="بارکد"
        value={barcode}
        onChange={(event) =>
          setBarcode(event.target.value)
        }
        fullWidth
        helperText={
          isEditMode
            ? "بارکد فعلی محصول را می‌توانید تغییر دهید."
            : "در صورت خالی بودن، بارکد به‌صورت خودکار تولید می‌شود."
        }
      />

      <FormControl fullWidth required>
        <InputLabel>دسته‌بندی</InputLabel>

        <Select
          value={category}
          label="دسته‌بندی"
          onChange={(event) =>
            setCategory(Number(event.target.value))
          }
          disabled={categoriesLoading}
        >
          {categories
            .filter((item) => item.is_active)
            .map((item) => (
              <MenuItem
                key={item.id}
                value={item.id}
              >
                {item.name}
              </MenuItem>
            ))}
        </Select>
      </FormControl>

      <TextField
        label="واحد"
        value={unit}
        onChange={(event) =>
          setUnit(event.target.value)
        }
        fullWidth
      />

      <TextField
        label="قیمت خرید"
        type="number"
        value={purchasePrice}
        onChange={(event) =>
          setPurchasePrice(event.target.value)
        }
        fullWidth
      />

      <TextField
        label="قیمت فروش"
        type="number"
        value={salePrice}
        onChange={(event) =>
          setSalePrice(event.target.value)
        }
        fullWidth
      />

      <FormControlLabel
        control={
          <Switch
            checked={isActive}
            onChange={(event) =>
              setIsActive(event.target.checked)
            }
          />
        }
        label="محصول فعال باشد"
      />

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
          disabled={loading || categoriesLoading}
        >
          {loading
            ? "در حال ذخیره..."
            : isEditMode
              ? "ذخیره تغییرات"
              : "ثبت محصول"}
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

export default ProductForm;