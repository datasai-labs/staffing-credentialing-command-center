import React from "react";
import { Box, Grid, Link, Stack, Typography } from "@mui/material";
import { Link as RouterLink, createSearchParams } from "react-router-dom";
import { Cell, Pie, PieChart, Tooltip as RTooltip } from "recharts";

import { useActionsSummary, useCredentialRisk, useCredentialRiskSummary, useKpis, useKpisTrend, useStaffingGaps, useStaffingSummary } from "../api/hooks";
import { ErrorState, LoadingSkeleton } from "../components/States";
import { StatCard } from "../components/StatCard";
import { ChartCard, ResponsiveChartContainer, Sparkline, useChartPalette } from "../components/charts";

export function Overview() {
  const pal = useChartPalette();
  const kpis = useKpis();
  const kpisTrend = useKpisTrend(30);
  const staffingSummary = useStaffingSummary({ risk_level: undefined });
  const credSummary = useCredentialRiskSummary({});
  const actionsSummary = useActionsSummary();
  const topStaffing = useStaffingGaps({
    risk_level: "HIGH",
    page: 1,
    page_size: 10,
    sort: "gap_count:desc"
  });
  const topCreds = useCredentialRisk({
    risk_bucket: "0-14,15-30",
    page: 1,
    page_size: 10,
    sort: "days_until_expiration:asc"
  });

  if (kpis.isLoading) return <LoadingSkeleton rows={6} />;
  if (kpis.isError) return <ErrorState message={(kpis.error as Error).message} onRetry={() => kpis.refetch()} />;
  if (!kpis.data) return <LoadingSkeleton rows={6} />;
  const d = kpis.data;

  const spark = kpisTrend.data?.points ?? [];
  const pendingSpark = spark.map((p) => ({ x: p.kpi_date, y: p.providers_pending }));
  const expSpark = spark.map((p) => ({ x: p.kpi_date, y: p.providers_expiring_30d }));
  const revSpark = spark.map((p) => ({ x: p.kpi_date, y: p.daily_revenue_at_risk_est }));

  const riskPie = (staffingSummary.data?.by_risk_level ?? []).map((r) => ({ name: r.label, value: r.count }));
  const bucketBar = credSummary.data?.by_bucket ?? [];

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Overview</Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <StatCard label="Providers total" value={d.providers_total} helper={`As of ${d.kpi_date}`} />
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard
            label="Providers pending"
            value={d.providers_pending}
            helper={kpisTrend.isLoading ? "Loading trend…" : undefined}
          />
          {pendingSpark.length ? <Sparkline data={pendingSpark} /> : null}
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard label="Expiring (<=30d)" value={d.providers_expiring_30d} />
          {expSpark.length ? <Sparkline data={expSpark} /> : null}
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard
            label="Daily revenue at risk (est.)"
            value={d.daily_revenue_at_risk_est.toLocaleString(undefined, { style: "currency", currency: "USD" })}
          />
          {revSpark.length ? <Sparkline data={revSpark} /> : null}
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <StatCard
            label="Open mitigation actions"
            value={actionsSummary.data?.open_count ?? 0}
            helper={actionsSummary.isLoading ? "Loading…" : actionsSummary.isError ? "Unavailable" : undefined}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard
            label="Median time-to-resolve (hrs)"
            value={actionsSummary.data?.median_time_to_resolve_hours != null ? actionsSummary.data.median_time_to_resolve_hours.toFixed(1) : "—"}
            helper="Resolved actions only"
          />
        </Grid>
        <Grid item xs={12} md={6} />
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Shift risk distribution"
            subtitle="Count of shifts by risk level"
            right={
              <Link
                component={RouterLink}
                to={{ pathname: "/staffing", search: createSearchParams({ risk_level: "HIGH" }).toString() }}
              >
                View high risk
              </Link>
            }
          >
            {staffingSummary.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : staffingSummary.isError ? (
              <ErrorState message={(staffingSummary.error as Error).message} onRetry={() => staffingSummary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={260}>
                <PieChart>
                  <RTooltip />
                  <Pie data={riskPie} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3}>
                    {riskPie.map((_, i) => (
                      <Cell key={i} fill={pal.categorical[i % pal.categorical.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard
            title="Credential risk buckets"
            subtitle="Counts by bucket"
            right={
              <Link
                component={RouterLink}
                to={{
                  pathname: "/credentials",
                  search: createSearchParams({ risk_bucket: "0-14,15-30" }).toString()
                }}
              >
                View expiring soon
              </Link>
            }
          >
            {credSummary.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : credSummary.isError ? (
              <ErrorState message={(credSummary.error as Error).message} onRetry={() => credSummary.refetch()} />
            ) : (
              <Stack spacing={0.75}>
                {bucketBar.map((b, i) => (
                  <Box
                    key={b.label}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      p: 1,
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 2,
                      bgcolor: "background.paper"
                    }}
                  >
                    <Box sx={{ width: 10, height: 10, borderRadius: 999, bgcolor: pal.categorical[i % pal.categorical.length] }} />
                    <Typography variant="body2" sx={{ width: 70 }}>
                      {b.label}
                    </Typography>
                    <Box sx={{ flex: 1, height: 8, borderRadius: 999, bgcolor: "rgba(15,23,42,0.08)" }}>
                      <Box
                        sx={{
                          height: 8,
                          borderRadius: 999,
                          width: `${Math.min(100, (b.count / Math.max(1, Math.max(...bucketBar.map((x) => x.count)))) * 100)}%`,
                          bgcolor: pal.categorical[i % pal.categorical.length]
                        }}
                      />
                    </Box>
                    <Typography variant="body2" sx={{ width: 40, textAlign: "right" }}>
                      {b.count}
                    </Typography>
                  </Box>
                ))}
                {!bucketBar.length ? (
                  <Typography variant="body2" color="text.secondary">
                    No data.
                  </Typography>
                ) : null}
              </Stack>
            )}
          </ChartCard>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Shifts at risk (top 10)"
            subtitle="Highest gap counts"
            right={
              <Link component={RouterLink} to={{ pathname: "/staffing", search: createSearchParams({ risk_level: "HIGH" }).toString() }}>
                Open table
              </Link>
            }
          >
            {topStaffing.isLoading ? (
              <LoadingSkeleton rows={6} />
            ) : topStaffing.isError ? (
              <ErrorState message={(topStaffing.error as Error).message} onRetry={() => topStaffing.refetch()} />
            ) : (
              <Box sx={{ mt: 0.5 }}>
            {(topStaffing.data?.items ?? []).map((r) => (
                  <Typography key={r.shift_id} variant="body2" sx={{ mb: 0.5 }}>
                    {r.facility_name ?? r.facility_id} • {new Date(r.start_ts).toLocaleString()} • gap={r.gap_count} • {r.risk_reason}
                  </Typography>
                ))}
            {!(topStaffing.data?.items ?? []).length ? (
                  <Typography variant="body2" color="text.secondary">
                    No high-risk shifts.
                  </Typography>
                ) : null}
              </Box>
            )}
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard
            title="Credentials expiring soon (top 10)"
            subtitle="Buckets 0-14 and 15-30"
            right={
              <Link
                component={RouterLink}
                to={{ pathname: "/credentials", search: createSearchParams({ risk_bucket: "0-14,15-30" }).toString() }}
              >
                Open table
              </Link>
            }
          >
            {topCreds.isLoading ? (
              <LoadingSkeleton rows={6} />
            ) : topCreds.isError ? (
              <ErrorState message={(topCreds.error as Error).message} onRetry={() => topCreds.refetch()} />
            ) : (
              <Box sx={{ mt: 0.5 }}>
            {(topCreds.data?.items ?? []).map((r) => (
                  <Typography key={r.event_id} variant="body2" sx={{ mb: 0.5 }}>
                    <Link component={RouterLink} to={`/providers/${r.provider_id}`}>
                      {r.provider_id}
                    </Link>{" "}
                    • {r.cred_type} • {r.risk_bucket} • days_left={r.days_until_expiration}
                  </Typography>
                ))}
            {!(topCreds.data?.items ?? []).length ? (
                  <Typography variant="body2" color="text.secondary">
                    No expiring credentials in selected buckets.
                  </Typography>
                ) : null}
              </Box>
            )}
          </ChartCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

