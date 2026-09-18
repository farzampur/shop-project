import React from "react";
import { Alert, Box, Button, Paper, Typography } from "@mui/material";

interface ErrorBoundaryState { hasError: boolean; }

export default class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    console.error("FRONTEND RUNTIME ERROR:", error, info);
  }

  handleReload = () => window.location.reload();

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", p: 2, direction: "rtl" }}>
        <Paper sx={{ width: "100%", maxWidth: 520, p: 3, textAlign: "right" }}>
          <Typography variant="h6" sx={{ mb: 1 }}>خطای غیرمنتظره</Typography>
          <Alert severity="error" sx={{ mb: 2 }}>
            اجرای این بخش از برنامه با مشکل مواجه شد. صفحه را دوباره بارگذاری کنید.
          </Alert>
          <Button variant="contained" onClick={this.handleReload}>بارگذاری مجدد</Button>
        </Paper>
      </Box>
    );
  }
}
