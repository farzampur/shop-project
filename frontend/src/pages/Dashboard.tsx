import { useEffect } from "react";
import { Box, Paper, Typography } from "@mui/material";
import { listProducts } from "../services/productService";
import { useStore } from "../contexts/StoreContext";


function Dashboard() {
  const { activeStore } = useStore();

  useEffect(() => {
    if (!activeStore) return;
    void listProducts(activeStore.id)
      .then((products) => console.log("PRODUCTS API SUCCESS:", products))
      .catch((error) => console.error("PRODUCTS API ERROR:", error));
  }, [activeStore]);
  return (
    <Box
      sx={{
        minHeight: "100vh",
        p: 4,
        direction: "rtl",
      }}
    >
      <Typography
        variant="h4"
        sx={{
          textAlign: "right",
          mb: 3,
        }}
      >
        داشبورد فروشگاه
      </Typography>

      <Paper
        elevation={2}
        sx={{
          p: 3,
        }}
      >
        <Typography>
          به سیستم مدیریت فروشگاه خوش آمدید.
        </Typography>
      </Paper>
    </Box>
  );
}

export default Dashboard;