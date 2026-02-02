import React, { useMemo, useState } from "react";
import { Box, Button, Card, CardContent, Checkbox, FormControlLabel, Stack, TextField, Typography } from "@mui/material";
import { GridColDef, GridRowSelectionModel } from "@mui/x-data-grid";

import { apiGet } from "../api/client";
import { useScenarioCoverage, useWorklistNoEligibleShifts } from "../api/hooks";
import { ScenarioCoverageRequest, ShiftRecommendations, StaffingGap } from "../api/types";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";
import { ErrorState } from "../components/States";
import { StatCard } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { formatDateTime } from "../utils/format";

function parseIds(text: string): string[] {
  const parts = text
    .split(/[\n,;\s]+/g)
    .map((s) => s.trim())
    .filter(Boolean);
  return Array.from(new Set(parts));
}

export function ScenarioPlanner() {
  const toast = useToast();
  const scenario = useScenarioCoverage();

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [facilityId, setFacilityId] = useState("");

  const [providerIdsText, setProviderIdsText] = useState("");
  const [fixAcls, setFixAcls] = useState(true);
  const [fixLicense, setFixLicense] = useState(false);
  const [assumePayer, setAssumePayer] = useState(false);
  const [assumePrivilege, setAssumePrivilege] = useState(false);

  const [tableState, setTableState] = useState<ServerTableState>({ page: 1, pageSize: 25, sort: "gap_count:desc" });
  const [selection, setSelection] = useState<GridRowSelectionModel>([]);

  const q = useWorklistNoEligibleShifts({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    facility_id: facilityId || undefined,
    risk_level: "HIGH",
    procedure_code: undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const cols: GridColDef[] = useMemo(
    () => [
      { field: "facility_name", headerName: "Facility", flex: 1, minWidth: 180 },
      { field: "start_ts", headerName: "Start", minWidth: 180, valueFormatter: (p: any) => formatDateTime(p?.value) },
      { field: "procedure_name", headerName: "Procedure", flex: 1, minWidth: 180 },
      { field: "gap_count", headerName: "Gap", type: "number", width: 90 },
      { field: "risk_reason", headerName: "Reason", flex: 1, minWidth: 220 }
    ],
    []
  );

  const selectedShiftIds = selection.map(String);
  const providerIds = parseIds(providerIdsText);

  const buildPayload = (): ScenarioCoverageRequest => ({
    shift_ids: selectedShiftIds,
    assumptions: {
      fix_acls_for_provider_ids: fixAcls ? providerIds : [],
      fix_license_for_provider_ids: fixLicense ? providerIds : [],
      assume_payer_for_provider_ids: assumePayer ? providerIds : [],
      assume_privilege_for_provider_ids: assumePrivilege ? providerIds : []
    }
  });

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Scenario planner</Typography>

      <Typography variant="body2" color="text.secondary">
        Demo tool: simulate “if we fix blockers for X providers, how many CRITICAL (HIGH) shifts become coverable?” No database writes—just app-layer
        recompute on recommended providers.
      </Typography>

      <FilterBar
        onReset={() => {
          setStartDate("");
          setEndDate("");
          setFacilityId("");
          setProviderIdsText("");
          setFixAcls(true);
          setFixLicense(false);
          setAssumePayer(false);
          setAssumePrivilege(false);
          setSelection([]);
          setTableState({ page: 1, pageSize: 25, sort: "gap_count:desc" });
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <TextField
            size="small"
            label="Facility ID"
            value={facilityId}
            onChange={(e) => setFacilityId(e.target.value)}
            placeholder="FAC-001"
            sx={{ minWidth: 180 }}
          />
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

      {q.isError ? <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} /> : null}

      <Typography variant="h6">1) Select high-risk shifts (no eligible providers)</Typography>

      <DataTable<StaffingGap>
        rows={q.data?.items ?? []}
        columns={cols}
        total={q.data?.total ?? 0}
        loading={q.isLoading || q.isFetching}
        state={tableState}
        onStateChange={setTableState}
        getRowId={(r) => r.shift_id}
        checkboxSelection
        rowSelectionModel={selection}
        onRowSelectionModelChange={setSelection}
        csvFileName="scenario_candidate_shifts"
        height={520}
      />

      <Typography variant="caption" color="text.secondary">
        Selected shifts: {selectedShiftIds.length}
      </Typography>

      <Typography variant="h6">2) Choose assumptions + provider set</Typography>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.25}>
            <TextField
              label="Provider IDs (comma/newline separated)"
              placeholder="PROV-001, PROV-002"
              value={providerIdsText}
              onChange={(e) => setProviderIdsText(e.target.value)}
              multiline
              minRows={3}
            />

            <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
              <FormControlLabel control={<Checkbox checked={fixAcls} onChange={(e) => setFixAcls(e.target.checked)} />} label="Assume ACLS fixed" />
              <FormControlLabel
                control={<Checkbox checked={fixLicense} onChange={(e) => setFixLicense(e.target.checked)} />}
                label="Assume license renewed"
              />
              <FormControlLabel
                control={<Checkbox checked={assumePrivilege} onChange={(e) => setAssumePrivilege(e.target.checked)} />}
                label="Assume privileges granted"
              />
              <FormControlLabel
                control={<Checkbox checked={assumePayer} onChange={(e) => setAssumePayer(e.target.checked)} />}
                label="Assume payer enrollment complete"
              />
            </Stack>

            <Stack direction={{ xs: "column", md: "row" }} spacing={1} alignItems="flex-start">
              <Button
                variant="outlined"
                disabled={!selectedShiftIds.length}
                onClick={async () => {
                  try {
                    const recs = await Promise.all(
                      selectedShiftIds.map((sid) =>
                        apiGet<ShiftRecommendations>(`/api/v1/shifts/${sid}/recommendations?include_providers=false`).catch(() => null as any)
                      )
                    );
                    const ids = Array.from(
                      new Set(
                        recs
                          .flatMap((r) => r?.recommended_provider_ids ?? [])
                          .map((s) => String(s))
                          .filter(Boolean)
                      )
                    );
                    setProviderIdsText(ids.join(", "));
                    toast.show(`Filled ${ids.length} provider IDs from recommendations`, "success");
                  } catch (e: any) {
                    toast.show(e?.message ?? "Failed to load recommendations", "error");
                  }
                }}
              >
                Fill provider IDs from selected shifts’ recommendations
              </Button>

              <Button
                variant="contained"
                disabled={scenario.isPending || selectedShiftIds.length === 0}
                onClick={async () => {
                  try {
                    const payload = buildPayload();
                    if (!payload.shift_ids.length) return;
                    await scenario.mutateAsync(payload);
                  } catch (e: any) {
                    toast.show(e?.message ?? "Scenario failed", "error");
                  }
                }}
              >
                Run scenario
              </Button>
            </Stack>

            {scenario.isError ? <ErrorState message={(scenario.error as Error).message} /> : null}
          </Stack>
        </CardContent>
      </Card>

      <Typography variant="h6">3) Results</Typography>

      {scenario.data ? (
        <Stack spacing={2}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Box sx={{ flex: 1 }}>
              <StatCard label="Selected shifts" value={scenario.data.shift_count} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <StatCard label="Baseline coverable" value={scenario.data.baseline_coverable_count} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <StatCard label="Scenario coverable" value={scenario.data.scenario_coverable_count} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <StatCard label="Delta coverable" value={scenario.data.delta_coverable_count} />
            </Box>
          </Stack>

          <Box sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 2, bgcolor: "background.paper" }}>
            <Typography variant="body2" color="text.secondary">
              Tip: in the demo, narrate this as “time-to-ready bottlenecks”: fixing certification/enrollment blockers unlocks coverage and reduces revenue
              leakage.
            </Typography>
          </Box>

          <DataTable<any>
            rows={scenario.data.results}
            columns={[
              { field: "shift_id", headerName: "Shift ID", width: 180 },
              { field: "baseline_coverable", headerName: "Baseline", width: 110, type: "boolean" },
              { field: "scenario_coverable", headerName: "Scenario", width: 110, type: "boolean" },
              { field: "delta_coverable", headerName: "Improved", width: 110, type: "boolean" },
              { field: "scenario_best_provider_id", headerName: "Provider (scenario)", width: 180 },
              {
                field: "scenario_changes",
                headerName: "Notes",
                flex: 1,
                minWidth: 220,
                valueFormatter: (p: any) => (Array.isArray(p?.value) ? p.value.join("; ") : "")
              }
            ]}
            total={scenario.data.results.length}
            loading={false}
            state={{ page: 1, pageSize: 50, sort: undefined }}
            onStateChange={() => {}}
            getRowId={(r: any) => r.shift_id}
            csvFileName="scenario_results"
            height={420}
          />
        </Stack>
      ) : (
        <Typography variant="body2" color="text.secondary">
          Run a scenario to see results.
        </Typography>
      )}
    </Stack>
  );
}

