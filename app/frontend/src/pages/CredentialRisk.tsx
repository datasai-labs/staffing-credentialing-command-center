import React, { useMemo, useState } from "react";
import { Box, Stack, TextField, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { useSearchParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Line, LineChart, Tooltip as RTooltip, XAxis, YAxis } from "recharts";

import { useCredentialRisk, useCredentialRiskSummary } from "../api/hooks";
import { CredentialRiskRow } from "../api/types";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar, SearchInput } from "../components/FilterBar";
import { ErrorState } from "../components/States";
import { ChartCard, ResponsiveChartContainer, useChartPalette } from "../components/charts";
import { formatDateTime } from "../utils/format";

function useDebounced<T>(value: T, delayMs: number): T {
  const [v, setV] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setV(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return v;
}

export function CredentialRisk() {
  const pal = useChartPalette();
  const [sp, setSp] = useSearchParams();

  const [providerId, setProviderId] = useState(sp.get("provider_id") ?? "");
  const [credType, setCredType] = useState(sp.get("cred_type") ?? "");
  const [bucket, setBucket] = useState(sp.get("risk_bucket") ?? "");

  const providerIdDeb = useDebounced(providerId, 400);
  const credTypeDeb = useDebounced(credType, 400);

  const [tableState, setTableState] = useState<ServerTableState>({
    page: Number(sp.get("page") ?? 1),
    pageSize: Number(sp.get("page_size") ?? 25),
    sort: sp.get("sort") ?? "days_until_expiration:asc"
  });

  const q = useCredentialRisk({
    provider_id: providerIdDeb || undefined,
    cred_type: credTypeDeb || undefined,
    risk_bucket: bucket || undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const summary = useCredentialRiskSummary({
    cred_type: credTypeDeb || undefined,
    risk_bucket: bucket || undefined
  });

  const columns: GridColDef[] = useMemo(
    () => [
      { field: "provider_id", headerName: "Provider ID", width: 170 },
      { field: "cred_type", headerName: "Credential", width: 190 },
      { field: "risk_bucket", headerName: "Bucket", width: 110 },
      { field: "days_until_expiration", headerName: "Days left", type: "number", width: 110 },
      {
        field: "expires_at",
        headerName: "Expires",
        width: 200,
        valueFormatter: (p: any) => formatDateTime(p?.value)
      },
      {
        field: "verified_at",
        headerName: "Verified",
        width: 200,
        valueFormatter: (p: any) => formatDateTime(p?.value)
      },
      { field: "source_system", headerName: "Source", width: 160 }
    ],
    []
  );

  const onStateChange = (s: ServerTableState) => {
    setTableState(s);
    const next = new URLSearchParams(sp);
    next.set("page", String(s.page));
    next.set("page_size", String(s.pageSize));
    if (s.sort) next.set("sort", s.sort);
    setSp(next, { replace: true });
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Credential risk</Typography>

      <FilterBar
        onReset={() => {
          setProviderId("");
          setCredType("");
          setBucket("");
          setSp(new URLSearchParams(), { replace: true });
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <SearchInput value={providerId} onChange={setProviderId} placeholder="Provider ID…" />
          <SearchInput value={credType} onChange={setCredType} placeholder="Credential type…" />
          <SearchInput value={bucket} onChange={setBucket} placeholder="Risk bucket (EXPIRED,0-14,15-30,31-90,>90)…" />
          <TextField
            size="small"
            label="Tip: buckets"
            value="EXPIRED, 0-14, 15-30, 31-90, >90"
            InputProps={{ readOnly: true }}
            sx={{ minWidth: 260 }}
          />
        </Stack>
      </FilterBar>

      <Stack direction={{ xs: "column", lg: "row" }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <ChartCard title="By risk bucket" subtitle="Count of credential events">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.by_bucket ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="label" tick={{ fill: pal.muted, fontSize: 12 }} />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" fill={pal.primary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="By credential type" subtitle="Count of credential events">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.by_cred_type ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="label" tick={{ fill: pal.muted, fontSize: 12 }} hide />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" fill={pal.secondary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="Expirations over time" subtitle="Count of expirations by week">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <LineChart data={summary.data?.expires_by_week ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="date" tick={{ fill: pal.muted, fontSize: 12 }} />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Line type="monotone" dataKey="count" stroke={pal.primary} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>
      </Stack>

      {q.isError ? <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} /> : null}

      <DataTable<CredentialRiskRow>
        rows={q.data?.items ?? []}
        columns={columns}
        total={q.data?.total ?? 0}
        loading={q.isLoading || q.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r) => r.event_id}
      />
    </Stack>
  );
}

