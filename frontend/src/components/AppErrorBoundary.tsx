import { Component, type ErrorInfo, type ReactNode } from "react";
import { Alert, Box, Button, Paper, Typography } from "@mui/material";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export default class AppErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("APP UI ERROR:", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", p: 2 }} dir="rtl">
        <Paper sx={{ width: "100%", maxWidth: 520, p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 800, mb: 1 }}>
            خطای غیرمنتظره در نمایش صفحه
          </Typography>
          <Alert severity="error" sx={{ mb: 2 }}>
            صفحه با خطای غیرمنتظره مواجه شد. می‌توانید نمایش صفحه را دوباره امتحان کنید.
          </Alert>
          <Button variant="contained" onClick={this.handleRetry}>
            تلاش مجدد
          </Button>
        </Paper>
      </Box>
    );
  }
}
