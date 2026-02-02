import React from "react";
import { Close } from "@mui/icons-material";
import { Box, Divider, Drawer, IconButton, Stack, Typography } from "@mui/material";

export function SidePanel({
  open,
  title,
  subtitle,
  width = 440,
  onClose,
  children
}: {
  open: boolean;
  title: string;
  subtitle?: React.ReactNode;
  width?: number;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width, p: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
              {title}
            </Typography>
            {subtitle ? (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          <IconButton onClick={onClose} size="small" aria-label="Close">
            <Close fontSize="small" />
          </IconButton>
        </Stack>
        <Divider sx={{ my: 1.5 }} />
        {children}
      </Box>
    </Drawer>
  );
}

