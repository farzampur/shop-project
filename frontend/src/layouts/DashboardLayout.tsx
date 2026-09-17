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
  FormControl,
  Select,
  MenuItem,
} from "@mui/material";
import { logout } from "../services/authService";
import type { SelectChangeEvent } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import InventoryIcon from "@mui/icons-material/Inventory";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import PointOfSaleIcon from "@mui/icons-material/PointOfSale";
import PeopleIcon from "@mui/icons-material/People";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import AssessmentIcon from "@mui/icons-material/Assessment";
import CategoryIcon from "@mui/icons-material/Category";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import LogoutIcon from "@mui/icons-material/Logout";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import LockClockIcon from "@mui/icons-material/LockClock";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import StorefrontIcon from "@mui/icons-material/Storefront";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import PriceChangeIcon from "@mui/icons-material/PriceChange";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import MenuOpenIcon from "@mui/icons-material/MenuOpen";
import MenuIcon from "@mui/icons-material/Menu";
import { useStore } from "../contexts/StoreContext";
import { canAccessRoute, type AppRouteKey } from "../services/routePermissions";

const drawerWidth = 220;
const collapsedDrawerWidth = 68;

type MenuItem = {
  key: AppRouteKey;
  title: string;
  path: string;
  icon: React.ReactNode;
};

const menuItems: readonly MenuItem[] = [
  { key: "dashboard", title: "داشبورد", path: "/dashboard", icon: <DashboardIcon /> },
  { key: "categories", title: "دسته‌بندی‌ها", path: "/categories", icon: <CategoryIcon /> },
  { key: "products", title: "محصولات", path: "/products", icon: <InventoryIcon /> },
  { key: "inventory", title: "موجودی", path: "/inventory", icon: <InventoryIcon /> },
  { key: "purchases", title: "خرید", path: "/purchases", icon: <ShoppingCartIcon /> },
  { key: "suppliers", title: "تأمین‌کنندگان", path: "/suppliers", icon: <LocalShippingIcon /> },
  { key: "sales", title: "فروش", path: "/sales", icon: <PointOfSaleIcon /> },
  { key: "customers", title: "مشتریان", path: "/customers", icon: <PeopleIcon /> },
  { key: "cashbox", title: "صندوق", path: "/cashbox", icon: <AccountBalanceIcon /> },
  { key: "reports", title: "گزارش‌ها", path: "/reports", icon: <AssessmentIcon /> },
  { key: "advancedReports", title: "گزارش‌های تکمیلی", path: "/advanced-reports", icon: <AssessmentIcon /> },
  { key: "cashClose", title: "بستن صندوق", path: "/cash-close", icon: <LockClockIcon /> },
  { key: "audit", title: "گزارش فعالیت", path: "/audit", icon: <FactCheckIcon /> },
  { key: "users", title: "کاربران و کارکنان", path: "/users", icon: <AdminPanelSettingsIcon /> },
  { key: "stores", title: "مدیریت شعب", path: "/stores", icon: <StorefrontIcon /> },
  { key: "transfers", title: "انتقال بین شعب", path: "/transfers", icon: <SwapHorizIcon /> },
  { key: "pricing", title: "قیمت‌گذاری", path: "/pricing", icon: <PriceChangeIcon /> },
];

const roleLabels = {
  manager: "مدیر",
  seller: "فروشنده",
  cashier: "صندوقدار",
  warehouse: "انباردار",
} as const;

function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(() => localStorage.getItem("dashboard_drawer_open") !== "false");
  const {
    user,
    activeRole,
    stores,
    activeStore,
    setActiveStore,
    loading: storeLoading,
  } = useStore();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const handleStoreChange = (event: SelectChangeEvent<number>) => {
    const storeId = Number(event.target.value);
    const selectedStore = stores.find((store) => store.id === storeId);
    if (selectedStore) setActiveStore(selectedStore);
  };

  const toggleDrawer = () => {
    setDrawerOpen((current) => {
      const next = !current;
      localStorage.setItem("dashboard_drawer_open", String(next));
      return next;
    });
  };

  const visibleMenuItems = menuItems.filter((item) =>
    canAccessRoute(item.key, activeRole),
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", direction: "rtl" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, right: drawerOpen ? 8 : 8, left: 8, top: 8, width: "auto", borderRadius: 3 }}>
        <Toolbar sx={{ minHeight: 54, gap: 1 }}>
          <ListItemButton onClick={toggleDrawer} sx={{ minWidth: 44, width: 44, height: 40, p: 0, justifyContent: "center", borderRadius: 2 }} aria-label={drawerOpen ? "بستن منو" : "باز کردن منو"}>
            {drawerOpen ? <MenuOpenIcon /> : <MenuIcon />}
          </ListItemButton>
          {drawerOpen && <Typography variant="h6" sx={{ mr: 1 }}>فروشگاه:</Typography>}
          <FormControl size="small" sx={{ minWidth: 220, backgroundColor: "white", borderRadius: 1 }}>
            <Select
              value={activeStore?.id ?? ""}
              onChange={handleStoreChange}
              displayEmpty
              disabled={storeLoading || stores.length === 0}
            >
              {stores.map((store) => (
                <MenuItem key={store.id} value={store.id}>{store.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />
          {drawerOpen && <Box sx={{ textAlign: "right" }}>
            <Typography variant="body2">
              {user?.first_name || user?.last_name
                ? `${user.first_name} ${user.last_name}`.trim()
                : user?.username}
            </Typography>
            <Typography variant="caption">
              {activeRole ? roleLabels[activeRole] : "بدون نقش"}
            </Typography>
          </Box>}
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        anchor="right"
        sx={{
          width: drawerOpen ? drawerWidth : collapsedDrawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerOpen ? drawerWidth : collapsedDrawerWidth,
            boxSizing: "border-box",
            top: 70,
            right: drawerOpen ? 8 : 8,
            height: "calc(100vh - 78px)",
            borderRadius: 3,
            overflow: "hidden",
            boxShadow: "0 12px 35px rgba(31,48,77,.12)",
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        <List sx={{ pt: 1, flex: 1, overflowY: "auto" }}>
          {visibleMenuItems.map((item) => {
            const selected = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
            return (
              <ListItemButton
                key={item.path}
                selected={selected}
                onClick={() => navigate(item.path)}
                sx={{ minHeight: 38, py: 0.25 }}
              >
                <ListItemIcon sx={{ minWidth: drawerOpen ? 34 : "auto", justifyContent: "center", "& .MuiSvgIcon-root": { fontSize: 20 } }}>{item.icon}</ListItemIcon>
                {drawerOpen && <ListItemText primary={item.title} sx={{ textAlign: "right", "& .MuiListItemText-primary": { fontSize: "0.82rem" } }} />}
              </ListItemButton>
            );
          })}
        </List>

        <Box sx={{ borderTop: "1px solid #e8edf5", p: 1, backgroundColor: "rgba(255,255,255,.96)" }}>
          <ListItemButton
            onClick={handleLogout}
            sx={{ minHeight: 40, py: 0.25, color: "error.main", fontWeight: 700 }}
          >
            <ListItemIcon sx={{ minWidth: drawerOpen ? 34 : "auto", color: "inherit", justifyContent: "center", "& .MuiSvgIcon-root": { fontSize: 20 } }}><LogoutIcon /></ListItemIcon>
            {drawerOpen && <ListItemText primary="خروج" sx={{ textAlign: "right", "& .MuiListItemText-primary": { fontSize: "0.84rem", fontWeight: 700 } }} />}
          </ListItemButton>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 1, mt: 8, mr: 0, transition: "margin .2s ease" }}>
        <Outlet />
      </Box>
    </Box>
  );
}

export default DashboardLayout;
