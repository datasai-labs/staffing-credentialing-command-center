import React from "react";
import { Box } from "@mui/material";
import { ResponsiveContainer } from "recharts";

export function ResponsiveChartContainer({
  height = 240,
  children
}: {
  height?: number;
  children: React.ReactNode;
}) {
  return (
    <Box sx={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        {children as any}
      </ResponsiveContainer>
    </Box>
  );
}

