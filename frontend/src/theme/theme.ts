import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  direction: "rtl",

  typography: {
    fontFamily: [
      "Tahoma",
      "Arial",
      "sans-serif",
    ].join(","),
  },

  components: {
    MuiTypography: {
      styleOverrides: {
        root: {
          direction: "rtl",
          textAlign: "right",
        },
      },
    },
  },

  palette: {
    mode: "light",

    primary: {
      main: "#1976d2",
    },

    secondary: {
      main: "#9c27b0",
    },
  },
});

export default theme;