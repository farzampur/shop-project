import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { refreshAccessToken, logout } from "../services/authService";
import { tokenService } from "../services/tokenService";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;

    const ensureSession = async () => {
      const accessToken = tokenService.getAccessToken();
      if (!accessToken) {
        if (mounted) setChecking(false);
        return;
      }

      try {
        if (tokenService.isAccessTokenExpired()) {
          if (!tokenService.getRefreshToken()) throw new Error("Refresh token not found");
          await refreshAccessToken();
        }
        if (mounted) setAuthenticated(true);
      } catch {
        logout();
        if (mounted) setAuthenticated(false);
      } finally {
        if (mounted) setChecking(false);
      }
    };

    void ensureSession();
    return () => { mounted = false; };
  }, []);

  if (checking) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!authenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default ProtectedRoute;
