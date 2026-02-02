import React from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import PeopleIcon from "@mui/icons-material/People";
import WarningIcon from "@mui/icons-material/Warning";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import PlaylistAddCheckIcon from "@mui/icons-material/PlaylistAddCheck";
import TuneIcon from "@mui/icons-material/Tune";
import LocalHospitalIcon from "@mui/icons-material/LocalHospital";

const drawerWidth = 240;

const navItems = [
  { label: "Overview", path: "/", icon: <DashboardIcon /> },
  { label: "Worklists", path: "/worklists", icon: <PlaylistAddCheckIcon /> },
  { label: "Staffing gaps", path: "/staffing", icon: <WarningIcon /> },
  { label: "Nurse staffing", path: "/nurse-staffing", icon: <LocalHospitalIcon /> },
  { label: "Providers", path: "/providers", icon: <PeopleIcon /> },
  { label: "Credential risk", path: "/credentials", icon: <FactCheckIcon /> },
  // { label: "Scenario planner", path: "/scenarios", icon: <TuneIcon /> }
];

export function App() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex", bgcolor: "background.default", minHeight: "100vh" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 800, letterSpacing: -0.2 }}>
            Staffing Command Center
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: "border-box" }
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto" }}>
          <List>
            {navItems.map((item) => (
              <ListItemButton
                key={item.path}
                selected={item.path === "/" ? location.pathname === "/" : location.pathname.startsWith(item.path)}
                onClick={() => navigate(item.path)}
                sx={{
                  mx: 1,
                  my: 0.5,
                  borderRadius: 2,
                  "&.Mui-selected": {
                    backgroundColor: "rgba(11, 95, 174, 0.10)"
                  },
                  "&.Mui-selected:hover": {
                    backgroundColor: "rgba(11, 95, 174, 0.14)"
                  }
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
          <Divider />
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}

