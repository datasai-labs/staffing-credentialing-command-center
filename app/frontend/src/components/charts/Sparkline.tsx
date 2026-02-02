import React from "react";
import { Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

import { useChartPalette } from "./chartTheme";
import { ResponsiveChartContainer } from "./ResponsiveChartContainer";

export type SparkPoint = { x: string; y: number };

export function Sparkline({ data }: { data: SparkPoint[] }) {
  const pal = useChartPalette();

  return (
    <ResponsiveChartContainer height={56}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <XAxis dataKey="x" hide />
        <YAxis hide domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ borderRadius: 10, borderColor: pal.divider }}
          labelStyle={{ color: pal.muted }}
          formatter={(value: any) => [value, "Value"]}
        />
        <Line type="monotone" dataKey="y" stroke={pal.primary} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveChartContainer>
  );
}

