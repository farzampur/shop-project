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
import { useStore } from "../contexts/StoreContext";
import LogoutIcon from "@mui/icons-material/Logout";

import {
  Outlet,
  useNavigate,
} from "react-router-dom";


const drawerWidth = 240;

function DashboardLayout() {
  const navigate = useNavigate();


  const {
    stores,
    activeStore,
    setActiveStore,
    loading: storeLoading,
  } = useStore();

	const handleLogout = () => {
	  logout();
	  navigate("/login", { replace: true });
	};

  const handleStoreChange = (
    event: SelectChangeEvent<number>
  ) => {
    const storeId = Number(
      event.target.value
    );

    const selectedStore = stores.find(
      (store) => store.id === storeId
    );

    if (!selectedStore) {
      return;
    }

    setActiveStore(selectedStore);
  };

  const menuItems = [
    {
      title: "داشبورد",
      path: "/dashboard",
      icon: <DashboardIcon />,
    },
	{
      title: "دسته‌بندی‌ها",
      path: "/categories",
      icon: <CategoryIcon />,
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
          zIndex: (theme) =>
            theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            sx={{
              mr: 2,
            }}
          >
            فروشگاه:
          </Typography>

          <FormControl
            size="small"
            sx={{
              minWidth: 220,
              backgroundColor: "white",
              borderRadius: 1,
            }}
          >
            <Select
              value={activeStore?.id ?? ""}
              onChange={handleStoreChange}
              displayEmpty
              disabled={
                storeLoading ||
                stores.length === 0
              }
            >
              {stores.map((store) => (
                <MenuItem
                  key={store.id}
                  value={store.id}
                >
                  {store.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />

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
              onClick={() =>
                navigate(item.path)
              }
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
		  <ListItemButton onClick={handleLogout}>
			<ListItemIcon>
			  <LogoutIcon />
			</ListItemIcon>

			<ListItemText
			  primary="خروج"
			  sx={{
				textAlign: "right",
			  }}
			/>
		  </ListItemButton>		  
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

