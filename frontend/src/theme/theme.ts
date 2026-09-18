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
      styleOverrides: {
        root: { minHeight: 36, fontSize: "0.86rem" },
        input: { paddingBlock: 8, paddingInline: 10 },
      },
    },
    MuiInputLabel: {
      styleOverrides: { root: { fontSize: "0.84rem" } },
    },
    MuiFormHelperText: {
      styleOverrides: { root: { marginTop: 3, fontSize: "0.72rem", lineHeight: 1.35 } },
    },
    MuiFormControlLabel: {
      styleOverrides: { root: { marginInline: 0, marginBlock: -2 }, label: { fontSize: "0.82rem" } },
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
    MuiTableContainer: {
      styleOverrides: { root: { width: "100%", overflowX: "auto" } },
    },
    MuiTable: {
      defaultProps: { size: "small" },
      styleOverrides: { root: { minWidth: 560 } },
    },
    MuiTableHead: {
      styleOverrides: { root: { "& .MuiTableCell-root": { fontSize: "0.76rem", fontWeight: 800, whiteSpace: "nowrap" } } },
    },
    MuiTableCell: {
      styleOverrides: { root: { padding: "5px 8px", fontSize: "0.8rem", lineHeight: 1.35, whiteSpace: "nowrap" } },
    },
    MuiTableRow: { styleOverrides: { root: { height: 38 } } },
    MuiToolbar: {
      styleOverrides: { regular: { minHeight: "48px !important", paddingInline: 12 } },
    },
    MuiDialogTitle: {
      styleOverrides: { root: { padding: "12px 16px", fontSize: "1rem", fontWeight: 800 } },
    },
    MuiDialogContent: {
      styleOverrides: { root: { padding: "8px 16px 12px", "&:first-of-type": { paddingTop: 8 } } },
    },
    MuiDialogActions: {
      styleOverrides: { root: { padding: "8px 16px 12px", gap: 6 } },
    },
    MuiMenuItem: {
      styleOverrides: { root: { minHeight: "34px !important", fontSize: "0.84rem" } },
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
