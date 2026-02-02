import React, { useMemo, useState } from "react";
import { Box, Chip, Link, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";

import {
  useShiftEligibilityExplain,
  useWorklistExpiringCredentials,
  useWorklistNoEligibleShifts,
  useWorklistProviderBlockers
} from "../api/hooks";
import { CredentialExpiringRow, ProviderBlockersRow, StaffingGap } from "../api/types";
import { ActionsPanel } from "../components/ActionsPanel";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar, SearchInput } from "../components/FilterBar";
import { SidePanel } from "../components/SidePanel";
import { EmptyState, ErrorState } from "../components/States";
import { formatDateTime } from "../utils/format";

function useDebounced<T>(value: T, delayMs: number): T {
  const [v, setV] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setV(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return v;
}

type TabKey = "shifts" | "credentials" | "providers";

export function Worklists() {
  const navigate = useNavigate();
  const [sp, setSp] = useSearchParams();
  const [tab, setTab] = useState<TabKey>((sp.get("tab") as TabKey) || "shifts");

  // Shared filters
  const [facilityId, setFacilityId] = useState(sp.get("facility_id") ?? "");
  const [specialty, setSpecialty] = useState(sp.get("specialty") ?? "");
  const [riskLevel, setRiskLevel] = useState(sp.get("risk_level") ?? "HIGH");
  const [bucket, setBucket] = useState(sp.get("risk_bucket") ?? "0-14,15-30");
  const [blocker, setBlocker] = useState(sp.get("blocker") ?? "");
  const [startDate, setStartDate] = useState(sp.get("start_date") ?? "");
  const [endDate, setEndDate] = useState(sp.get("end_date") ?? "");

  const debFacilityId = useDebounced(facilityId, 400);
  const debSpecialty = useDebounced(specialty, 400);

  const [tableState, setTableState] = useState<ServerTableState>({
    page: Number(sp.get("page") ?? 1),
    pageSize: Number(sp.get("page_size") ?? 25),
    sort: sp.get("sort") ?? (tab === "credentials" ? "days_until_expiration:asc" : "gap_count:desc")
  });

  const [selectedShift, setSelectedShift] = useState<StaffingGap | null>(null);
  const [selectedCred, setSelectedCred] = useState<CredentialExpiringRow | null>(null);
  const [selectedProv, setSelectedProv] = useState<ProviderBlockersRow | null>(null);

  const shiftExplain = useShiftEligibilityExplain(selectedShift?.shift_id);

  const shifts = useWorklistNoEligibleShifts({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    facility_id: debFacilityId || undefined,
    risk_level: riskLevel || undefined,
    procedure_code: undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const creds = useWorklistExpiringCredentials({
    facility_id: debFacilityId || undefined,
    specialty: debSpecialty || undefined,
    provider_id: undefined,
    cred_type: undefined,
    risk_bucket: bucket || undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const providers = useWorklistProviderBlockers({
    facility_id: debFacilityId || undefined,
    specialty: debSpecialty || undefined,
    blocker: blocker || undefined,
    page: tableState.page,
    page_size: tableState.pageSize,
    sort: tableState.sort
  });

  const onStateChange = (s: ServerTableState) => {
    setTableState(s);
    const next = new URLSearchParams(sp);
    next.set("tab", tab);
    next.set("page", String(s.page));
    next.set("page_size", String(s.pageSize));
    if (s.sort) next.set("sort", s.sort);
    setSp(next, { replace: true });
  };

  const shiftCols: GridColDef[] = useMemo(
    () => [
      { field: "facility_name", headerName: "Facility", flex: 1, minWidth: 180 },
      { field: "start_ts", headerName: "Start", minWidth: 180, valueFormatter: (p: any) => formatDateTime(p?.value) },
      { field: "procedure_name", headerName: "Procedure", flex: 1, minWidth: 180 },
      { field: "gap_count", headerName: "Gap", type: "number", width: 90 },
      { field: "risk_level", headerName: "Risk", width: 110 },
      { field: "risk_reason", headerName: "Reason", flex: 1, minWidth: 220 }
    ],
    []
  );

  const credCols: GridColDef[] = useMemo(
    () => [
      { field: "provider_name", headerName: "Provider", flex: 1, minWidth: 180 },
      { field: "provider_id", headerName: "Provider ID", width: 160 },
      { field: "home_facility_name", headerName: "Facility", width: 180 },
      { field: "specialty", headerName: "Specialty", width: 180 },
      { field: "cred_type", headerName: "Credential", width: 180 },
      { field: "risk_bucket", headerName: "Bucket", width: 110 },
      { field: "days_until_expiration", headerName: "Days left", type: "number", width: 110 },
      { field: "expires_at", headerName: "Expires", width: 190, valueFormatter: (p: any) => formatDateTime(p?.value) }
    ],
    []
  );

  const provCols: GridColDef[] = useMemo(
    () => [
      { field: "provider_name", headerName: "Provider", flex: 1, minWidth: 180 },
      { field: "provider_id", headerName: "Provider ID", width: 160 },
      { field: "home_facility_name", headerName: "Facility", width: 180 },
      { field: "specialty", headerName: "Specialty", width: 180 },
      {
        field: "blockers",
        headerName: "Blockers",
        width: 220,
        valueFormatter: (p: any) => (Array.isArray(p?.value) ? p.value.join(", ") : "")
      },
      { field: "time_to_ready_days", headerName: "Time-to-ready (d)", type: "number", width: 150 }
    ],
    []
  );

  const active = tab === "shifts" ? shifts : tab === "credentials" ? creds : providers;
  const rows = active.data?.items ?? [];
  const total = active.data?.total ?? 0;

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Worklists</Typography>

      <Tabs
        value={tab}
        onChange={(_, v) => {
          setTab(v);
          setSelectedShift(null);
          setSelectedCred(null);
          setSelectedProv(null);
          setTableState((s) => ({ ...s, page: 1 }));
          const next = new URLSearchParams(sp);
          next.set("tab", v);
          next.set("page", "1");
          setSp(next, { replace: true });
        }}
      >
        <Tab value="shifts" label="Shifts: no eligible providers" />
        <Tab value="credentials" label="Credentials: expiring soon" />
        <Tab value="providers" label="Providers: readiness blockers" />
      </Tabs>

      <FilterBar
        onReset={() => {
          setFacilityId("");
          setSpecialty("");
          setRiskLevel("HIGH");
          setBucket("0-14,15-30");
          setBlocker("");
          setStartDate("");
          setEndDate("");
          setSp(new URLSearchParams({ tab }), { replace: true });
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <SearchInput value={facilityId} onChange={setFacilityId} placeholder="Facility ID…" />
          {tab === "shifts" ? (
            <>
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
            </>
          ) : tab === "credentials" ? (
            <>
              <SearchInput value={specialty} onChange={setSpecialty} placeholder="Specialty…" />
              <SearchInput value={bucket} onChange={setBucket} placeholder="Risk bucket (0-14,15-30,...)…" />
            </>
          ) : (
            <>
              <SearchInput value={specialty} onChange={setSpecialty} placeholder="Specialty…" />
              <SearchInput value={blocker} onChange={setBlocker} placeholder="Blocker filter (LICENSE/ACLS/PRIVILEGE/PAYER)…" />
            </>
          )}
        </Stack>
      </FilterBar>

      {active.isError ? <ErrorState message={(active.error as Error).message} onRetry={() => active.refetch()} /> : null}

      <DataTable<any>
        rows={rows}
        columns={tab === "shifts" ? shiftCols : tab === "credentials" ? credCols : provCols}
        total={total}
        loading={active.isLoading || active.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r: any) => (tab === "credentials" ? r.event_id : tab === "providers" ? r.provider_id : r.shift_id)}
        onRowClick={(r: any) => {
          if (tab === "shifts") setSelectedShift(r as StaffingGap);
          else if (tab === "credentials") setSelectedCred(r as CredentialExpiringRow);
          else setSelectedProv(r as ProviderBlockersRow);
        }}
        csvFileName={`worklist_${tab}`}
      />

      <SidePanel
        open={Boolean(selectedShift)}
        onClose={() => setSelectedShift(null)}
        title="Shift worklist item"
        subtitle={
          selectedShift
            ? `${selectedShift.facility_name ?? selectedShift.facility_id} • ${new Date(selectedShift.start_ts).toLocaleString()}`
            : undefined
        }
        width={520}
      >
        {selectedShift ? (
          <Stack spacing={1.5}>
            <Typography variant="body2">
              {selectedShift.procedure_name} • gap={selectedShift.gap_count} • risk={selectedShift.risk_level}
            </Typography>

            <Link
              component={RouterLink}
              to={{ pathname: "/staffing", search: new URLSearchParams({ risk_level: selectedShift.risk_level }).toString() }}
            >
              Open in Staffing gaps
            </Link>

            <Typography variant="h6">Eligibility (recommended providers)</Typography>
            {shiftExplain.isLoading ? (
              <Typography variant="body2" color="text.secondary">
                Loading…
              </Typography>
            ) : shiftExplain.isError ? (
              <ErrorState message={(shiftExplain.error as Error).message} onRetry={() => shiftExplain.refetch()} />
            ) : shiftExplain.data?.providers?.length ? (
              <Stack spacing={1}>
                {shiftExplain.data.providers.map((p) => (
                  <Box
                    key={p.provider_id}
                    sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 2, bgcolor: "background.paper" }}
                  >
                    <Stack spacing={0.5}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {p.provider_name ?? p.provider_id}
                        </Typography>
                        <Chip size="small" label={p.is_eligible ? "Eligible" : "Blocked"} color={p.is_eligible ? "success" : "warning"} />
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        {p.specialty ?? "—"} • license_days_left={p.state_license_days_left ?? "—"} • acls_days_left={p.acls_days_left ?? "—"} • priv=
                        {p.active_privilege_count ?? "—"} • payer={p.active_payer_count ?? "—"}
                      </Typography>
                      {!p.is_eligible ? (
                        <Typography variant="body2">
                          {p.why_not.slice(0, 2).join(" • ") || "Blocked"}{" "}
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
                ))}
              </Stack>
            ) : (
              <EmptyState title="No recommendations" description="This shift has no recommended providers to explain." />
            )}

            <ActionsPanel entityType="SHIFT" entityId={selectedShift.shift_id} facilityId={selectedShift.facility_id} defaultActionType="OUTREACH" />
          </Stack>
        ) : null}
      </SidePanel>

      <SidePanel
        open={Boolean(selectedCred)}
        onClose={() => setSelectedCred(null)}
        title="Credential expiring"
        subtitle={selectedCred ? `${selectedCred.provider_name ?? selectedCred.provider_id} • ${selectedCred.cred_type}` : undefined}
        width={520}
      >
        {selectedCred ? (
          <Stack spacing={1.25}>
            <Typography variant="body2">
              Bucket: {selectedCred.risk_bucket} • days_left={selectedCred.days_until_expiration} • expires={new Date(selectedCred.expires_at).toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Facility: {selectedCred.home_facility_name ?? selectedCred.home_facility_id ?? "—"} • Specialty: {selectedCred.specialty ?? "—"}
            </Typography>
            <Link component={RouterLink} to={`/providers/${selectedCred.provider_id}`}>
              Open provider detail
            </Link>
            <ActionsPanel entityType="PROVIDER" entityId={selectedCred.provider_id} facilityId={selectedCred.home_facility_id ?? undefined} defaultActionType="CREDENTIAL_EXPEDITE" />
          </Stack>
        ) : null}
      </SidePanel>

      <SidePanel
        open={Boolean(selectedProv)}
        onClose={() => setSelectedProv(null)}
        title="Provider readiness blocker"
        subtitle={selectedProv ? `${selectedProv.provider_name} (${selectedProv.provider_id})` : undefined}
        width={520}
      >
        {selectedProv ? (
          <Stack spacing={1.25}>
            <Typography variant="body2">
              Blockers: {(selectedProv.blockers ?? []).join(", ") || "—"}{" "}
              {selectedProv.time_to_ready_days != null ? (
                <Typography component="span" variant="caption" color="text.secondary">
                  (est. time-to-ready: {selectedProv.time_to_ready_days}d)
                </Typography>
              ) : null}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Facility: {selectedProv.home_facility_name ?? selectedProv.home_facility_id} • Specialty: {selectedProv.specialty}
            </Typography>
            <Link component={RouterLink} to={`/providers/${selectedProv.provider_id}`}>
              Open provider detail
            </Link>
            <ActionsPanel
              entityType="PROVIDER"
              entityId={selectedProv.provider_id}
              facilityId={selectedProv.home_facility_id}
              defaultActionType={(selectedProv.blockers ?? []).includes("PAYER") ? "PAYER_ENROLLMENT_FOLLOWUP" : "PRIVILEGE_REQUEST"}
            />
          </Stack>
        ) : null}
      </SidePanel>
    </Stack>
  );
}

