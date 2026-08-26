import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import Products from "./pages/products/Products";

function App() {
  return (
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
          <Route path="/dashboard" element={<Dashboard />} />

          {/* فعلاً صفحات آزمایشی */}
          <Route
            path="/products"
            element={<Products />}
          />

          <Route
            path="/purchases"
            element={<h2>خریدها</h2>}
          />

          <Route
            path="/sales"
            element={<h2>فروش‌ها</h2>}
          />

          <Route
            path="/customers"
            element={<h2>مشتریان</h2>}
          />

          <Route
            path="/cashbox"
            element={<h2>صندوق</h2>}
          />

          <Route
            path="/reports"
            element={<h2>گزارش‌ها</h2>}
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
  );
}

export default App;