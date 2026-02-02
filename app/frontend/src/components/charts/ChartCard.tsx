import React from "react";
import { Card, CardContent, Stack, Typography } from "@mui/material";

export function ChartCard({
  title,
  subtitle,
  right,
  children
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Stack spacing={0.25}>
            <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
              {title}
            </Typography>
            {subtitle ? (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            ) : null}
          </Stack>
          {right ? <Stack>{right}</Stack> : null}
        </Stack>
        <div style={{ marginTop: 12 }}>{children}</div>
      </CardContent>
    </Card>
  );
}

