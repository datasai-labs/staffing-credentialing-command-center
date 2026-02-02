import { useTheme } from "@mui/material/styles";

export function useChartPalette() {
  const theme = useTheme();
  const primary = theme.palette.primary.main;
  const secondary = theme.palette.secondary.main;
  const text = theme.palette.text.primary;
  const muted = theme.palette.text.secondary;
  const divider = theme.palette.divider;

  // Calm, clinical palette (avoid overly saturated colors).
  const categorical = [
    primary,
    "#2A9D8F",
    "#E9C46A",
    "#F4A261",
    "#E76F51",
    secondary,
    "#7C3AED",
    "#64748B"
  ];

  return { primary, secondary, text, muted, divider, categorical };
}

