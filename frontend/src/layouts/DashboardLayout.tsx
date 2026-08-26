import {
  AppBar,
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";

import DashboardIcon from "@mui/icons-material/Dashboard";
import InventoryIcon from "@mui/icons-material/Inventory";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import PointOfSaleIcon from "@mui/icons-material/PointOfSale";
import PeopleIcon from "@mui/icons-material/People";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import AssessmentIcon from "@mui/icons-material/Assessment";

import { Outlet, useNavigate } from "react-router-dom";

const drawerWidth = 240;

function DashboardLayout() {
  const navigate = useNavigate();

  const menuItems = [
    {
      title: "داشبورد",
      path: "/dashboard",
      icon: <DashboardIcon />,
    },
    {
      title: "محصولات",
      path: "/products",
      icon: <InventoryIcon />,
    },
    {
      title: "خرید",
      path: "/purchases",
      icon: <ShoppingCartIcon />,
    },
    {
      title: "فروش",
      path: "/sales",
      icon: <PointOfSaleIcon />,
    },
    {
      title: "مشتریان",
      path: "/customers",
      icon: <PeopleIcon />,
    },
    {
      title: "صندوق",
      path: "/cashbox",
      icon: <AccountBalanceIcon />,
    },
    {
      title: "گزارش‌ها",
      path: "/reports",
      icon: <AssessmentIcon />,
    },
  ];

  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        direction: "rtl",
      }}
    >
      {/* Header */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            sx={{
              flexGrow: 1,
              textAlign: "right",
            }}
          >
            فروشگاه من
          </Typography>

          <Typography variant="body2">
            مدیریت فروشگاه
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        anchor="right"
        sx={{
          width: drawerWidth,
          flexShrink: 0,

          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            top: 64,
          },
        }}
      >
        <List sx={{ pt: 2 }}>
          {menuItems.map((item) => (
            <ListItemButton
              key={item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>

              <ListItemText
                primary={item.title}
                sx={{
                  textAlign: "right",
                }}
              />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}

export default DashboardLayout;