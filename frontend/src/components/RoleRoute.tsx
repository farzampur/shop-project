import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import { Navigate, useLocation } from "react-router-dom";
import { useStore } from "../contexts/StoreContext";
import type { StoreRole } from "../services/authTypes";

interface RoleRouteProps {
  allowedRoles: readonly StoreRole[];
  children: React.ReactNode;
}

export default function RoleRoute({ allowedRoles, children }: RoleRouteProps) {
  const { activeRole, loading, stores } = useStore();
  const location = useLocation();

  if (loading) {
    return (
      <Box sx={{ minHeight: 240, display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!activeRole || stores.length === 0) {
    return <Navigate to="/dashboard" replace state={{ from: location.pathname }} />;
  }

  if (!allowedRoles.includes(activeRole)) {
    return <Navigate to="/dashboard" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
