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
import LogoutIcon from "@mui/icons-material/Logout";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useStore } from "../contexts/StoreContext";
import { canAccessRoute, type AppRouteKey } from "../services/routePermissions";

const drawerWidth = 240;

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
  { key: "sales", title: "فروش", path: "/sales", icon: <PointOfSaleIcon /> },
  { key: "customers", title: "مشتریان", path: "/customers", icon: <PeopleIcon /> },
  { key: "cashbox", title: "صندوق", path: "/cashbox", icon: <AccountBalanceIcon /> },
  { key: "reports", title: "گزارش‌ها", path: "/reports", icon: <AssessmentIcon /> },
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
  const {
    user,
    activeRole,
    stores,
    activeStore,
    setActiveStore,
    loading: storeLoading,
  } = useStore();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleStoreChange = (event: SelectChangeEvent<number>) => {
    const storeId = Number(event.target.value);
    const selectedStore = stores.find((store) => store.id === storeId);
    if (selectedStore) setActiveStore(selectedStore);
  };

  const visibleMenuItems = menuItems.filter((item) =>
    canAccessRoute(item.key, activeRole),
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", direction: "rtl" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ mr: 2 }}>فروشگاه:</Typography>
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
          <Box sx={{ textAlign: "right" }}>
            <Typography variant="body2">
              {user?.first_name || user?.last_name
                ? `${user.first_name} ${user.last_name}`.trim()
                : user?.username}
            </Typography>
            <Typography variant="caption">
              {activeRole ? roleLabels[activeRole] : "بدون نقش"}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        anchor="right"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box", top: 64 },
        }}
      >
        <List sx={{ pt: 2 }}>
          {visibleMenuItems.map((item) => {
            const selected = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
            return (
              <ListItemButton
                key={item.path}
                selected={selected}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.title} sx={{ textAlign: "right" }} />
              </ListItemButton>
            );
          })}
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon><LogoutIcon /></ListItemIcon>
            <ListItemText primary="خروج" sx={{ textAlign: "right" }} />
          </ListItemButton>
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Outlet />
      </Box>
    </Box>
  );
}

export default DashboardLayout;
