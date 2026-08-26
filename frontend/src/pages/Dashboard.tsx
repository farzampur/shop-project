import { useEffect } from "react";
import { Box, Paper, Typography } from "@mui/material";
import api from "../services/api";


function Dashboard() {
  useEffect(() => {
    api.get("/products/products/")
      .then((response) => {
        console.log("PRODUCTS API SUCCESS:", response.data);
      })
      .catch((error) => {
        console.error("PRODUCTS API ERROR:", error.response?.status);
        console.error("PRODUCTS API DATA:", error.response?.data);
      });
  }, []);
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