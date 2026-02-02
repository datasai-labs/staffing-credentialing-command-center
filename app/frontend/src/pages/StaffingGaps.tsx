import React, { useMemo, useState } from "react";
import { Box, Chip, Divider, Stack, TextField, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { useSearchParams } from "react-router-dom";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Tooltip as RTooltip, XAxis, YAxis } from "recharts";

import { useShiftEligibilityExplain, useShiftPrediction, useShiftRecommendations, useStaffingGaps, useStaffingSummary } from "../api/hooks";
import { StaffingGap } from "../api/types";
import { ActionsPanel } from "../components/ActionsPanel";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar, SearchInput } from "../components/FilterBar";
import { SidePanel } from "../components/SidePanel";
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

export function StaffingGaps() {
  const pal = useChartPalette();
  const [sp, setSp] = useSearchParams();
  const [facilityId, setFacilityId] = useState(sp.get("facility_id") ?? "");
  const [procedureCode, setProcedureCode] = useState(sp.get("procedure_code") ?? "");
  const [riskLevel, setRiskLevel] = useState(sp.get("risk_level") ?? "");
  const [startDate, setStartDate] = useState(sp.get("start_date") ?? "");
  const [endDate, setEndDate] = useState(sp.get("end_date") ?? "");

  const debFacilityId = useDebounced(facilityId, 400);
  const debProcedureCode = useDebounced(procedureCode, 400);

  const [tableState, setTableState] = useState<ServerTableState>({
    page: Number(sp.get("page") ?? 1),
    pageSize: Number(sp.get("page_size") ?? 25),
    sort: sp.get("sort") ?? "gap_count:desc"
  });

  const [selected, setSelected] = useState<StaffingGap | null>(null);
  const recs = useShiftRecommendations(selected?.shift_id);
  const pred = useShiftPrediction(selected?.shift_id ?? undefined);
  const explain = useShiftEligibilityExplain(selected?.shift_id ?? undefined);

  const q = useStaffingGaps({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    facility_id: debFacilityId || undefined,
    risk_level: riskLevel || undefined,
    procedure_code: debProcedureCode || undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const summary = useStaffingSummary({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    facility_id: debFacilityId || undefined,
    risk_level: riskLevel || undefined,
    procedure_code: debProcedureCode || undefined
  });

  const columns: GridColDef[] = useMemo(
    () => [
      { field: "facility_name", headerName: "Facility", flex: 1, minWidth: 180 },
      {
        field: "start_ts",
        headerName: "Start",
        flex: 1,
        minWidth: 180,
        valueFormatter: (p: any) => formatDateTime(p?.value)
      },
      {
        field: "end_ts",
        headerName: "End",
        flex: 1,
        minWidth: 180,
        valueFormatter: (p: any) => formatDateTime(p?.value)
      },
      { field: "procedure_name", headerName: "Procedure", flex: 1, minWidth: 180 },
      { field: "required_count", headerName: "Required", type: "number", width: 100 },
      { field: "assigned_count", headerName: "Assigned", type: "number", width: 100 },
      { field: "eligible_provider_count", headerName: "Eligible", type: "number", width: 100 },
      { field: "gap_count", headerName: "Gap", type: "number", width: 90 },
      { field: "risk_level", headerName: "Risk", width: 110 },
      { field: "risk_reason", headerName: "Reason", flex: 1, minWidth: 200 }
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
      <Typography variant="h5">Staffing gaps</Typography>

      <FilterBar
        onReset={() => {
          setFacilityId("");
          setProcedureCode("");
          setRiskLevel("");
          setStartDate("");
          setEndDate("");
          setSp(new URLSearchParams(), { replace: true });
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <SearchInput value={facilityId} onChange={setFacilityId} placeholder="Facility ID…" />
          <SearchInput value={procedureCode} onChange={setProcedureCode} placeholder="Procedure code…" />
          <SearchInput value={riskLevel} onChange={setRiskLevel} placeholder="Risk level (e.g. HIGH) or HIGH,MEDIUM…" />
          <TextField
            size="small"
            type="date"
            label="Start date"
            InputLabelProps={{ shrink: true }}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            sx={{ minWidth: 160 }}
          />
          <TextField
            size="small"
            type="date"
            label="End date"
            InputLabelProps={{ shrink: true }}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            sx={{ minWidth: 160 }}
          />
        </Stack>
      </FilterBar>

      <Stack direction={{ xs: "column", lg: "row" }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <ChartCard title="Daily gap volume" subtitle="Sum of gap_count by day">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <AreaChart data={summary.data?.daily_gap_count ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="date" tick={{ fill: pal.muted, fontSize: 12 }} />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Area type="monotone" dataKey="value" stroke={pal.primary} fill="rgba(11,95,174,0.18)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="Top facilities" subtitle="By total gap_count">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.top_facilities ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="facility_name" tick={{ fill: pal.muted, fontSize: 12 }} hide />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="total_gap_count" fill={pal.primary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>

        <Box sx={{ flex: 1 }}>
          <ChartCard title="Top procedures" subtitle="By total gap_count">
            {summary.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : summary.isError ? (
              <ErrorState message={(summary.error as Error).message} onRetry={() => summary.refetch()} />
            ) : (
              <ResponsiveChartContainer height={220}>
                <BarChart data={summary.data?.top_procedures ?? []} margin={{ left: 8, right: 16, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={String(pal.divider)} />
                  <XAxis dataKey="procedure_name" tick={{ fill: pal.muted, fontSize: 12 }} hide />
                  <YAxis tick={{ fill: pal.muted, fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="total_gap_count" fill={pal.secondary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveChartContainer>
            )}
          </ChartCard>
        </Box>
      </Stack>

      {q.isError ? <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} /> : null}

      <DataTable<StaffingGap>
        rows={q.data?.items ?? []}
        columns={columns}
        total={q.data?.total ?? 0}
        loading={q.isLoading || q.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r) => r.shift_id}
        onRowClick={(r) => setSelected(r)}
        csvFileName="staffing_gaps"
      />

      <SidePanel
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        title="Shift"
        subtitle={
          selected
            ? `${selected.facility_name ?? selected.facility_id} • ${new Date(selected.start_ts).toLocaleString()} → ${new Date(selected.end_ts).toLocaleString()}`
            : undefined
        }
        width={480}
      >
        {selected ? (
          <Stack spacing={1.5}>
            <Typography variant="body2">
              {selected.procedure_name} • gap={selected.gap_count} • risk={selected.risk_level}
            </Typography>

            <Divider />
            <Typography variant="h6">Predicted gap risk</Typography>
            {pred.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading prediction…
              </Typography>
            ) : pred.isError ? (
              <ErrorState message={(pred.error as Error).message} onRetry={() => pred.refetch()} />
            ) : pred.data?.predicted_gap_prob != null ? (
              <Stack spacing={0.5}>
                <Typography variant="body2">
                  Probability: {(pred.data.predicted_gap_prob * 100).toFixed(0)}% • Predicted gap: {pred.data.predicted_is_gap ?? "—"}
                </Typography>
                <Box sx={{ height: 10, borderRadius: 999, bgcolor: "rgba(15,23,42,0.08)" }}>
                  <Box
                    sx={{
                      height: 10,
                      borderRadius: 999,
                      width: `${Math.max(0, Math.min(100, pred.data.predicted_gap_prob * 100))}%`,
                      bgcolor:
                        pred.data.predicted_gap_prob >= 0.66 ? "#E76F51" : pred.data.predicted_gap_prob >= 0.33 ? "#E9C46A" : "#2A9D8F"
                    }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Scored at: {pred.data.scored_at ? new Date(pred.data.scored_at).toLocaleString() : "—"}
                </Typography>
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No prediction available for this shift.
              </Typography>
            )}

            <Typography variant="h6" sx={{ mt: 1 }}>
              Eligibility (recommended providers)
            </Typography>

            {explain.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading eligibility…
              </Typography>
            ) : explain.isError ? (
              <ErrorState message={(explain.error as Error).message} onRetry={() => explain.refetch()} />
            ) : (
              <Stack spacing={1}>
                {(explain.data?.providers ?? []).length ? (
                  explain.data!.providers.map((p) => (
                    <Box
                      key={p.provider_id}
                      sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 2, bgcolor: "background.paper" }}
                    >
                      <Stack spacing={0.5}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>
                            {p.provider_name ?? p.provider_id}{" "}
                            <Typography component="span" variant="caption" color="text.secondary">
                              ({p.provider_id})
                            </Typography>
                          </Typography>
                          <Chip
                            size="small"
                            label={p.is_eligible ? "Eligible" : "Blocked"}
                            color={p.is_eligible ? "success" : "warning"}
                            variant={p.is_eligible ? "filled" : "outlined"}
                          />
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          {p.specialty ?? "—"} • status={p.provider_status ?? "—"} • license_days_left={p.state_license_days_left ?? "—"} • acls_days_left=
                          {p.acls_days_left ?? "—"} • priv={p.active_privilege_count ?? "—"} • payer={p.active_payer_count ?? "—"}
                        </Typography>
                        {!p.is_eligible ? (
                          <Typography variant="body2">
                            {p.why_not.slice(0, 2).join(" • ") || "Blocked (unknown reason)"}{" "}
                            {p.time_to_ready_days != null ? (
                              <Typography component="span" variant="caption" color="text.secondary">
                                (est. time-to-ready: {p.time_to_ready_days}d)
                              </Typography>
                            ) : null}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            {p.why_eligible.slice(0, 2).join(" • ") || "Eligible"}
                          </Typography>
                        )}
                      </Stack>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No recommended providers found for this shift.
                  </Typography>
                )}
              </Stack>
            )}

            <Divider />
            <Typography variant="h6">Recommendations (raw)</Typography>
            {recs.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading recommendations…
              </Typography>
            ) : recs.isError ? (
              <ErrorState message={(recs.error as Error).message} onRetry={() => recs.refetch()} />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Provider IDs: {(recs.data?.recommended_provider_ids ?? []).join(", ") || "None"}
              </Typography>
            )}

            <Divider />
            <ActionsPanel entityType="SHIFT" entityId={selected.shift_id} facilityId={selected.facility_id} defaultActionType="OUTREACH" />
          </Stack>
        ) : null}
      </SidePanel>
    </Stack>
  );
}

