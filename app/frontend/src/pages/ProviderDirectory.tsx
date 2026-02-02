import React, { useMemo, useState } from "react";
import { Box, Stack, TextField, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Tooltip as RTooltip, XAxis, YAxis } from "recharts";

import { useProviders, useProvidersSummary } from "../api/hooks";
import { Provider360 } from "../api/types";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar, SearchInput } from "../components/FilterBar";
import { ErrorState } from "../components/States";
import { ChartCard, ResponsiveChartContainer, useChartPalette } from "../components/charts";

function useDebounced<T>(value: T, delayMs: number): T {
  const [v, setV] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setV(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return v;
}

export function ProviderDirectory() {
  const pal = useChartPalette();
  const navigate = useNavigate();
  const [sp, setSp] = useSearchParams();

  const [qText, setQText] = useState(sp.get("q") ?? "");
  const [specialty, setSpecialty] = useState(sp.get("specialty") ?? "");
  const [status, setStatus] = useState(sp.get("status") ?? "");
  const [expDays, setExpDays] = useState(sp.get("expiring_within_days") ?? "");

  const qDeb = useDebounced(qText, 400);
  const specialtyDeb = useDebounced(specialty, 400);

  const [tableState, setTableState] = useState<ServerTableState>({
    page: Number(sp.get("page") ?? 1),
    pageSize: Number(sp.get("page_size") ?? 25),
    sort: sp.get("sort") ?? "provider_name:asc"
  });

  const query = useProviders({
    q: qDeb || undefined,
    specialty: specialtyDeb || undefined,
    status: status || undefined,
    expiring_within_days: expDays ? Number(expDays) : undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const summary = useProvidersSummary({
    specialty: specialtyDeb || undefined,
    status: status || undefined,
    expiring_within_days: expDays ? Number(expDays) : undefined
  });

  const columns: GridColDef[] = useMemo(
    () => [
      { field: "provider_id", headerName: "Provider ID", width: 170 },
      { field: "provider_name", headerName: "Name", flex: 1, minWidth: 180 },
      { field: "specialty", headerName: "Specialty", width: 180 },
      { field: "provider_status", headerName: "Status", width: 120 },
      { field: "home_facility_name", headerName: "Home facility", width: 180 },
      { field: "state_license_days_left", headerName: "License days left", type: "number", width: 150 },
      { field: "acls_days_left", headerName: "ACLS days left", type: "number", width: 140 },
      { field: "active_privilege_count", headerName: "Active priv", type: "number", width: 120 },
      { field: "active_privilege_facility_count", headerName: "Facility count", type: "number", width: 130 }
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
      <Typography variant="h5">Provider directory</Typography>

      <FilterBar
        onReset={() => {
          setQText("");
          setSpecialty("");
          setStatus("");
          setExpDays("");
          setSp(new URLSearchParams(), { replace: true });
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <SearchInput value={qText} onChange={setQText} placeholder="Search by name or provider_id…" />
          <SearchInput value={specialty} onChange={setSpecialty} placeholder="Specialty…" />
          <SearchInput value={status} onChange={setStatus} placeholder="Status (ACTIVE/INACTIVE/ON_LEAVE)…" />
          <TextField
            size="small"
            label="Expiring within (days)"
            value={expDays}
            onChange={(e) => setExpDays(e.target.value)}
            sx={{ minWidth: 170 }}
          />
        </Stack>
      </FilterBar>

      <Stack direction={{ xs: "column", lg: "row" }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <ChartCard title="Specialty mix" subtitle="Providers by specialty">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.by_specialty ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="label" tick={{ fill: pal.muted, fontSize: 12 }} hide />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" fill={pal.primary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="Expiring funnel" subtitle="Min(days_left) thresholds">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.expiring_funnel ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="label" tick={{ fill: pal.muted, fontSize: 12 }} />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" fill="#E9C46A" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="Readiness score" subtitle="0–5 simple readiness distribution">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.readiness_histogram ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="label" tick={{ fill: pal.muted, fontSize: 12 }} />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" fill={pal.secondary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>
      </Stack>

      {query.isError ? <ErrorState message={(query.error as Error).message} onRetry={() => query.refetch()} /> : null}

      <DataTable<Provider360>
        rows={query.data?.items ?? []}
        columns={columns}
        total={query.data?.total ?? 0}
        loading={query.isLoading || query.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r) => r.provider_id}
        onRowClick={(row) => navigate(`/providers/${row.provider_id}`)}
      />
    </Stack>
  );
}

