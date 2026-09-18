import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  direction: "rtl",
  typography: {
    fontFamily: "Tahoma, Arial, sans-serif",
    fontSize: 13,
    h4: { fontWeight: 800, fontSize: "1.65rem" },
    h5: { fontWeight: 800, fontSize: "1.35rem" },
    h6: { fontWeight: 800, fontSize: "1.1rem" },
    body1: { fontSize: "0.9rem" },
    body2: { fontSize: "0.82rem" },
  },
  palette: {
    mode: "light",
    primary: { main: "#2563eb" },
    secondary: { main: "#7c3aed" },
    success: { main: "#16805b" },
    warning: { main: "#b7791f" },
    error: { main: "#c53030" },
    background: { default: "#f5f7fb", paper: "#fff" },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        html: { fontSize: "14px", direction: "rtl" },
        body: { fontSize: "0.9rem", direction: "rtl", textAlign: "right" },
        "#root": { direction: "rtl", minHeight: "100vh" },
      },
    },
    MuiTypography: {
      styleOverrides: { root: { direction: "rtl", textAlign: "right" } },
    },
    MuiButton: {
      defaultProps: { disableElevation: true, size: "small" },
      styleOverrides: { root: { minHeight: 34, paddingInline: 11, borderRadius: 9, fontWeight: 700 } },
    },
    MuiIconButton: {
      styleOverrides: { root: { padding: 7 } },
    },
    MuiTextField: { defaultProps: { size: "small" } },
    MuiFormControl: { defaultProps: { size: "small" } },
    MuiInputBase: {
      styleOverrides: { root: { minHeight: 38 } },
    },
    MuiCard: {
      styleOverrides: { root: { borderRadius: 14 } },
    },
    MuiCardContent: {
      styleOverrides: { root: { padding: 15, "&:last-child": { paddingBottom: 15 } } },
    },
    MuiPaper: {
      styleOverrides: { root: { borderRadius: 12 } },
    },
    MuiTableCell: { styleOverrides: { root: { padding: "6px 9px" } } },
    MuiTableRow: { styleOverrides: { root: { height: 40 } } },
    MuiToolbar: {
      styleOverrides: { regular: { minHeight: "50px !important" } },
    },
    MuiListItemButton: {
      styleOverrides: { root: { minHeight: 36, paddingBlock: 3 } },
    },
    MuiListItemIcon: {
      styleOverrides: { root: { minWidth: 32 } },
    },
  },
});

export default theme;
