import { createTheme } from "@mui/material";

// "Clinical/EHR" inspired theme (clean, dense, familiar) without copying any proprietary UI.
export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#0B5FAE" },
    secondary: { main: "#2A6F97" },
    background: {
      default: "#F5F7FA",
      paper: "#FFFFFF"
    },
    divider: "rgba(15, 23, 42, 0.12)",
    text: {
      primary: "#0F172A",
      secondary: "rgba(15, 23, 42, 0.72)"
    }
  },
  typography: {
    fontFamily:
      'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Noto Sans", "Helvetica Neue", sans-serif',
    h5: { fontWeight: 700, letterSpacing: -0.3 },
    h6: { fontWeight: 700, letterSpacing: -0.2 },
    overline: { letterSpacing: 0.8 }
  },
  shape: {
    borderRadius: 10
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: "#F5F7FA"
        }
      }
    },
    MuiAppBar: {
      defaultProps: {
        color: "transparent",
        elevation: 0
      },
      styleOverrides: {
        root: {
          borderBottom: "1px solid rgba(15, 23, 42, 0.12)",
          backdropFilter: "saturate(180%) blur(10px)"
        }
      }
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: 56
        }
      }
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: "1px solid rgba(15, 23, 42, 0.12)",
          backgroundImage:
            "linear-gradient(180deg, rgba(11, 95, 174, 0.06) 0%, rgba(255, 255, 255, 0) 28%)"
        }
      }
    },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: {
        root: {
          borderColor: "rgba(15, 23, 42, 0.12)"
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600
        }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600
        }
      }
    },
    MuiTextField: {
      defaultProps: {
        size: "small"
      }
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10
        }
      }
    }
  }
});

