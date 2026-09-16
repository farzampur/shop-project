import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  direction: "rtl",
  typography: {
    fontFamily: "Tahoma, Arial, sans-serif",
    h4: { fontWeight: 800 },
    h5: { fontWeight: 800 },
    h6: { fontWeight: 800 },
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
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        html: { fontSize: "14px" },
        body: { fontSize: "0.95rem" },
      },
    },
    MuiTypography: {
      styleOverrides: { root: { direction: "rtl", textAlign: "right" } },
    },
    MuiButton: { defaultProps: { disableElevation: true, size: "small" } },
    MuiTextField: { defaultProps: { size: "small" } },
    MuiFormControl: { defaultProps: { size: "small" } },
    MuiTableCell: { styleOverrides: { root: { padding: "7px 10px" } } },
  },
});

export default theme;
