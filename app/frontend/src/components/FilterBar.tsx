import React from "react";
import { Box, Button, Stack, TextField } from "@mui/material";

export function FilterBar({
  children,
  onReset
}: {
  children: React.ReactNode;
  onReset?: () => void;
}) {
  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} alignItems="center">
        <Box sx={{ flex: 1, width: "100%" }}>{children}</Box>
        {onReset ? (
          <Button variant="text" onClick={onReset} sx={{ whiteSpace: "nowrap" }}>
            Reset
          </Button>
        ) : null}
      </Stack>
    </Box>
  );
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search…"
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <TextField
      size="small"
      fullWidth
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

