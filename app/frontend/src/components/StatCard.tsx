import React from "react";
import { Card, CardContent, Typography } from "@mui/material";

export function StatCard({
  label,
  value,
  helper
}: {
  label: string;
  value: React.ReactNode;
  helper?: string;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5" sx={{ mt: 0.5 }}>
          {value}
        </Typography>
        {helper ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {helper}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

