import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import { ROUTE_ROLES } from "./services/routePermissions";
import DashboardLayout from "./layouts/DashboardLayout";
const Products = lazy(() => import("./pages/products/Products"));
const Inventory = lazy(() => import("./pages/inventory/Inventory"));
const Categories = lazy(() => import("./pages/categories/Categories"));
import { StoreProvider } from "./contexts/StoreContext";
const Purchases = lazy(() => import("./pages/purchases/Purchases"));
const Suppliers = lazy(() => import("./pages/suppliers/Suppliers"));
const Sales = lazy(() => import("./pages/sales/Sales"));
const Reports = lazy(() => import("./pages/Reports"));
const FinancialReports = lazy(() => import("./pages/FinancialReports"));
const Customers = lazy(() => import("./pages/customers/Customers"));
const Cashbox = lazy(() => import("./pages/cashbox/Cashbox"));
const CashDayClose = lazy(() => import("./pages/cashbox/CashDayClose"));
const AuditLogs = lazy(() => import("./pages/audit/AuditLogs"));
const Users = lazy(() => import("./pages/management/Users"));
const Stores = lazy(() => import("./pages/management/Stores"));
const StockTransfers = lazy(() => import("./pages/transfers/StockTransfers"));
const Pricing = lazy(() => import("./pages/pricing/Pricing"));
const AdvancedReports = lazy(() => import("./pages/AdvancedReports"));
const AccountingDashboard = lazy(() => import("./pages/accounting/AccountingDashboard"));
const ChartOfAccounts = lazy(() => import("./pages/accounting/ChartOfAccounts"));
const AccountingPeriods = lazy(() => import("./pages/accounting/AccountingPeriods"));
const JournalEntries = lazy(() => import("./pages/accounting/JournalEntries"));
const AccountingReports = lazy(() => import("./pages/accounting/AccountingReports"));

function App() {
  return (
   <StoreProvider>
    <BrowserRouter>
      <Suspense fallback={<div className="route-loading" role="status">در حال بارگذاری…</div>}>
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

          <Route path="/cash-close" element={<RoleRoute allowedRoles={ROUTE_ROLES.cashClose}><CashDayClose /></RoleRoute>} />
          <Route path="/audit" element={<RoleRoute allowedRoles={ROUTE_ROLES.audit}><AuditLogs /></RoleRoute>} />
          <Route path="/users" element={<RoleRoute allowedRoles={ROUTE_ROLES.users}><Users /></RoleRoute>} />
          <Route path="/stores" element={<RoleRoute allowedRoles={ROUTE_ROLES.stores}><Stores /></RoleRoute>} />
          <Route path="/transfers" element={<RoleRoute allowedRoles={ROUTE_ROLES.transfers}><StockTransfers /></RoleRoute>} />
          <Route path="/pricing" element={<RoleRoute allowedRoles={ROUTE_ROLES.pricing}><Pricing /></RoleRoute>} />
          <Route path="/advanced-reports" element={<RoleRoute allowedRoles={ROUTE_ROLES.advancedReports}><AdvancedReports /></RoleRoute>} />

          <Route path="/accounting" element={<RoleRoute allowedRoles={ROUTE_ROLES.accountingDashboard}><AccountingDashboard /></RoleRoute>} />
          <Route path="/accounting/accounts" element={<RoleRoute allowedRoles={ROUTE_ROLES.accountingAccounts}><ChartOfAccounts /></RoleRoute>} />
          <Route path="/accounting/periods" element={<RoleRoute allowedRoles={ROUTE_ROLES.accountingPeriods}><AccountingPeriods /></RoleRoute>} />
          <Route path="/accounting/entries" element={<RoleRoute allowedRoles={ROUTE_ROLES.accountingEntries}><JournalEntries /></RoleRoute>} />
          <Route path="/accounting/reports" element={<RoleRoute allowedRoles={ROUTE_ROLES.accountingReports}><AccountingReports /></RoleRoute>} />


          <Route
            path="/reports"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.reports}>
                <Reports />
              </RoleRoute>
            }
          />

          <Route
            path="/financial-reports"
            element={
              <RoleRoute allowedRoles={ROUTE_ROLES.financialReports}>
                <FinancialReports />
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
      </Suspense>
    </BrowserRouter>
   </StoreProvider>
	
  );
}

export default App;