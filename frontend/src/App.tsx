import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import { ROUTE_ROLES } from "./services/routePermissions";
import DashboardLayout from "./layouts/DashboardLayout";
import Products from "./pages/products/Products";
import Inventory from "./pages/inventory/Inventory";
import Categories from "./pages/categories/Categories";
import { StoreProvider } from "./contexts/StoreContext";
import Purchases from "./pages/purchases/Purchases";
import Suppliers from "./pages/suppliers/Suppliers";
import Sales from "./pages/sales/Sales";
import Reports from "./pages/Reports";
import Customers from "./pages/customers/Customers";
import Cashbox from "./pages/cashbox/Cashbox";

function App() {
  return (
   <StoreProvider>
    <BrowserRouter>
      <Routes>
        {/* Login */}
        <Route path="/login" element={<Login />} />

        {/* Protected Area */}
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route
            path="/dashboard"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.dashboard}>
                <Dashboard />
              </RoleRoute>
            }
          />

          {/* فعلاً صفحات آزمایشی */}         
		  <Route
            path="/products"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.products}>
                <Products />
              </RoleRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.inventory}>
                <Inventory />
              </RoleRoute>
            }
          />

		  <Route
            path="/categories"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.categories}>
                <Categories />
              </RoleRoute>
            }
          />
		  <Route
            path="/purchases"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.purchases}>
                <Purchases />
              </RoleRoute>
            }
          />

          <Route
            path="/suppliers"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.suppliers}>
                <Suppliers />
              </RoleRoute>
            }
          />

          <Route
            path="/sales"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.sales}>
                <Sales />
              </RoleRoute>
            }
          />

          <Route
            path="/customers"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.customers}>
                <Customers />
              </RoleRoute>
            }
          />

          <Route
            path="/cashbox"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.cashbox}>
                <Cashbox />
              </RoleRoute>
            }
          />

          <Route
            path="/reports"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.reports}>
                <Reports />
              </RoleRoute>
            }
          />
        </Route>

        {/* Root */}
        <Route
          path="/"
          element={<Navigate to="/dashboard" replace />}
        />

        {/* Unknown routes */}
        <Route
          path="*"
          element={<Navigate to="/dashboard" replace />}
        />
      </Routes>
    </BrowserRouter>
   </StoreProvider>
	
  );
}

export default App;