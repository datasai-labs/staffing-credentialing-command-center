import React, { useMemo } from "react";
import { Box, Chip, Link, Stack, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { Link as RouterLink, useParams } from "react-router-dom";
import { CartesianGrid, ReferenceLine, Scatter, ScatterChart, Tooltip as RTooltip, XAxis, YAxis } from "recharts";

import { useProvider } from "../api/hooks";
import { CredentialRiskRow } from "../api/types";
import { ActionsPanel } from "../components/ActionsPanel";
import { DataTable, ServerTableState } from "../components/DataTable";
import { ErrorState, LoadingSkeleton } from "../components/States";
import { ChartCard, ResponsiveChartContainer, useChartPalette } from "../components/charts";
import { formatDateTime } from "../utils/format";

export function ProviderDetail() {
  const pal = useChartPalette();
  const { id } = useParams();
  const q = useProvider(id ?? "");

  const [tableState, setTableState] = React.useState<ServerTableState>({
    page: 1,
    pageSize: 25,
    sort: "days_until_expiration:asc"
  });

  const cols: GridColDef[] = useMemo(
    () => [
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

  if (q.isLoading) return <LoadingSkeleton rows={10} />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  if (!q.data) return <LoadingSkeleton rows={10} />;

  const p = q.data.provider;
  const riskRows = q.data.credential_risk_rows;

  const warn = (p.state_license_days_left ?? 9999) <= 30 || (p.acls_days_left ?? 9999) <= 30;

  // Client-side paginate/sort for the embedded table (provider endpoint returns finite list).
  const start = (tableState.page - 1) * tableState.pageSize;
  const end = start + tableState.pageSize;
  const sortField = tableState.sort?.split(":")[0] ?? "days_until_expiration";
  const sortDir = tableState.sort?.split(":")[1] ?? "asc";
  const sorted = [...riskRows].sort((a: any, b: any) => {
    const av = a[sortField];
    const bv = b[sortField];
    if (av === bv) return 0;
    if (av === undefined || av === null) return 1;
    if (bv === undefined || bv === null) return -1;
    return sortDir === "asc" ? (av > bv ? 1 : -1) : av > bv ? -1 : 1;
  });

  const pageRows = sorted.slice(start, end);

  const timeline = riskRows.map((r: CredentialRiskRow) => ({
    cred_type: r.cred_type,
    expires_at: new Date(r.expires_at).getTime(),
    days: r.days_until_expiration
  }));
  const nowTs = Date.now();

  return (
    <Stack spacing={2}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h5">{p.provider_name}</Typography>
        <Link component={RouterLink} to="/providers">
          Back to directory
        </Link>
      </Stack>

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={`Status: ${p.provider_status}`} color={p.provider_status === "ACTIVE" ? "success" : "default"} />
        <Chip label={`Specialty: ${p.specialty}`} variant="outlined" />
        <Chip label={`Home: ${p.home_facility_name ?? p.home_facility_id}`} variant="outlined" />
        {p.state_license_status ? <Chip label={`License: ${p.state_license_status}`} /> : null}
        {p.acls_status ? <Chip label={`ACLS: ${p.acls_status}`} /> : null}
      </Stack>

      <Box>
        <Typography variant="h6">Risk</Typography>
        <Typography variant="body2" color={warn ? "error" : "text.secondary"}>
          License days left: {p.state_license_days_left ?? "—"} • ACLS days left: {p.acls_days_left ?? "—"}
        </Typography>
      </Box>

      <ChartCard title="Credential expiry timeline" subtitle="Expiration dates relative to today">
        {timeline.length ? (
          <ResponsiveChartContainer height={220}>
            <ScatterChart margin={{ left: 12, right: 16, top: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
              <XAxis
                type="number"
                dataKey="expires_at"
                domain={["auto", "auto"]}
                tick={{ fill: pal.muted, fontSize: 12 }}
                tickFormatter={(v) => new Date(Number(v)).toLocaleDateString()}
              />
              <YAxis type="number" dataKey="days" tick={{ fill: pal.muted, fontSize: 12 }} />
              <RTooltip
                formatter={(value: any, name: any, props: any) => [value, name]}
                labelFormatter={(v) => `Expires: ${new Date(Number(v)).toLocaleString()}`}
              />
              <ReferenceLine x={nowTs} stroke={pal.primary} strokeDasharray="4 4" />
              <Scatter data={timeline} fill={pal.primary} />
            </ScatterChart>
          </ResponsiveChartContainer>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No credential rows to plot.
          </Typography>
        )}
      </ChartCard>

      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">Credential risk (recent)</Typography>
        <Link
          component={RouterLink}
          to={`/credentials?${new URLSearchParams({ provider_id: p.provider_id }).toString()}`}
        >
          View all credential risk
        </Link>
      </Stack>

      <ChartCard title="Action log" subtitle="Closed-loop mitigation (outreach, credential expedite, etc.)">
        <ActionsPanel entityType="PROVIDER" entityId={p.provider_id} facilityId={p.home_facility_id} defaultActionType="CREDENTIAL_EXPEDITE" />
      </ChartCard>

      <DataTable<CredentialRiskRow>
        rows={pageRows}
        columns={cols}
        total={riskRows.length}
        loading={false}
        state={tableState}
        onStateChange={setTableState}
        getRowId={(r) => r.event_id}
      />
    </Stack>
  );
}

