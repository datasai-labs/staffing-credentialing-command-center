import React, { useMemo, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Stack,
  Tab,
  Tabs,
  Typography
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

import {
  useCostBreakdown,
  useCredentialGaps,
  useNurseStaffingKpis,
  useNurseStaffingSummary,
  useUnitDetail
} from "../api/hooks";
import { CredentialGapRow, NurseStaffingSummary } from "../api/types";
import { DataTable, ServerTableState } from "../components/DataTable";
import { FilterBar, SearchInput } from "../components/FilterBar";
import { SidePanel } from "../components/SidePanel";
import { EmptyState, ErrorState, LoadingState } from "../components/States";

type TabKey = "ratios" | "outsourced" | "credential_gaps";

const UNIT_TYPES = ["ICU", "STEP_DOWN", "MED_SURG", "TELEMETRY", "ED", "OR", "NICU"];

// Color scheme for staffing status
const STATUS_COLORS: Record<string, string> = {
  UNDERSTAFFED: "#ef4444",
  OPTIMAL: "#22c55e",
  OVERSTAFFED: "#f59e0b"
};

// Color scheme for employment types
const EMPLOYMENT_COLORS: Record<string, string> = {
  INTERNAL: "#3b82f6",
  CONTRACT: "#f59e0b",
  AGENCY: "#ef4444"
};

function StatCard({
  title,
  value,
  subtitle,
  color
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}) {
  return (
    <Card sx={{ minWidth: 160 }}>
      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 700, color: color ?? "text.primary" }}>
          {value}
        </Typography>
        {subtitle ? (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

function RatioGauge({ current, required }: { current: number; required: number }) {
  const ratio = required > 0 ? (current / required) * 100 : 100;
  const capped = Math.min(ratio, 150);
  let color = "#22c55e"; // green
  if (ratio < 90) color = "#ef4444"; // red - understaffed
  else if (ratio > 110) color = "#f59e0b"; // yellow - overstaffed

  return (
    <Box sx={{ width: "100%", maxWidth: 180 }}>
      <LinearProgress
        variant="determinate"
        value={Math.min(capped, 100)}
        sx={{
          height: 8,
          borderRadius: 4,
          bgcolor: "rgba(0,0,0,0.08)",
          "& .MuiLinearProgress-bar": { bgcolor: color }
        }}
      />
      <Typography variant="caption" color="text.secondary">
        {current}/{required} ({Math.round(ratio)}%)
      </Typography>
    </Box>
  );
}

export function NurseStaffing() {
  const [tab, setTab] = useState<TabKey>("ratios");
  const [facilityId, setFacilityId] = useState("");
  const [unitType, setUnitType] = useState("");
  const [staffingStatus, setStaffingStatus] = useState("");
  const [gapSeverity, setGapSeverity] = useState("");

  const [tableState, setTableState] = useState<ServerTableState>({
    page: 1,
    pageSize: 25,
    sort: "staffing_status:desc"
  });

  const [selectedUnit, setSelectedUnit] = useState<NurseStaffingSummary | null>(null);
  const [selectedGap, setSelectedGap] = useState<CredentialGapRow | null>(null);

  // API calls
  const kpis = useNurseStaffingKpis({ facility_id: facilityId || undefined });
  const summary = useNurseStaffingSummary({
    facility_id: facilityId || undefined,
    unit_type: unitType || undefined,
    staffing_status: staffingStatus || undefined,
    page: tableState.page,
    page_size: tableState.pageSize
  });
  const credentialGaps = useCredentialGaps({
    facility_id: facilityId || undefined,
    unit_type: unitType || undefined,
    gap_severity: gapSeverity || undefined,
    page: tableState.page,
    page_size: tableState.pageSize
  });
  const costBreakdown = useCostBreakdown({ facility_id: facilityId || undefined });
  const unitDetail = useUnitDetail(selectedUnit?.unit_id);

  const onStateChange = (s: ServerTableState) => {
    setTableState(s);
  };

  // Ratio monitor columns
  const ratioCols: GridColDef[] = useMemo(
    () => [
      { field: "unit_name", headerName: "Unit", flex: 1, minWidth: 160 },
      { field: "unit_type", headerName: "Type", width: 100 },
      { field: "facility_name", headerName: "Facility", flex: 1, minWidth: 160 },
      { field: "current_census", headerName: "Census", type: "number", width: 90 },
      { field: "nurses_required", headerName: "Required", type: "number", width: 100 },
      { field: "nurses_assigned", headerName: "Assigned", type: "number", width: 100 },
      {
        field: "staffing_ratio",
        headerName: "Ratio",
        width: 200,
        renderCell: (p) => (
          <RatioGauge current={p.row.nurses_assigned} required={p.row.nurses_required} />
        )
      },
      {
        field: "staffing_status",
        headerName: "Status",
        width: 140,
        renderCell: (p) => (
          <Chip
            size="small"
            label={p.value}
            sx={{
              bgcolor: STATUS_COLORS[p.value as string] ?? "#64748b",
              color: "white",
              fontWeight: 600
            }}
          />
        )
      },
      {
        field: "labor_cost_daily",
        headerName: "Daily Cost",
        type: "number",
        width: 120,
        valueFormatter: (p: any) => (p?.value ? `$${Math.round(p.value).toLocaleString()}` : "—")
      }
    ],
    []
  );

  // Credential gaps columns
  const gapCols: GridColDef[] = useMemo(
    () => [
      { field: "unit_name", headerName: "Unit", flex: 1, minWidth: 160 },
      { field: "unit_type", headerName: "Type", width: 100 },
      { field: "facility_name", headerName: "Facility", flex: 1, minWidth: 160 },
      { field: "required_cred_type", headerName: "Certification", flex: 1, minWidth: 180 },
      { field: "nurses_assigned", headerName: "Assigned", type: "number", width: 100 },
      { field: "nurses_with_cert", headerName: "With Cert", type: "number", width: 100 },
      { field: "nurses_missing_cert", headerName: "Missing", type: "number", width: 100 },
      {
        field: "gap_severity",
        headerName: "Severity",
        width: 120,
        renderCell: (p) => {
          const colors: Record<string, string> = {
            LOW: "#64748b",
            MEDIUM: "#f59e0b",
            HIGH: "#f97316",
            CRITICAL: "#ef4444"
          };
          return (
            <Chip
              size="small"
              label={p.value}
              sx={{ bgcolor: colors[p.value as string] ?? "#64748b", color: "white", fontWeight: 600 }}
            />
          );
        }
      }
    ],
    []
  );

  // Pie chart data for cost breakdown
  const pieData = useMemo(() => {
    if (!costBreakdown.data?.breakdown_by_type) return [];
    return costBreakdown.data.breakdown_by_type.map((item) => ({
      name: item.employment_type,
      value: item.total_cost,
      percentage: item.percentage_of_total,
      nurses: item.nurse_count
    }));
  }, [costBreakdown.data]);

  const renderKpis = () => {
    if (kpis.isLoading) return <LoadingState />;
    if (kpis.isError) return <ErrorState message={kpis.error?.message} onRetry={() => kpis.refetch()} />;
    const data = kpis.data;
    if (!data) return null;

    return (
      <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", gap: 2 }}>
        <StatCard title="Nurses on Shift" value={data.total_nurses_on_shift} />
        <StatCard title="Units Understaffed" value={data.units_understaffed} color={data.units_understaffed > 0 ? "#ef4444" : undefined} />
        <StatCard title="Units Optimal" value={data.units_optimal} color="#22c55e" />
        <StatCard title="Units Overstaffed" value={data.units_overstaffed} color={data.units_overstaffed > 0 ? "#f59e0b" : undefined} />
        <StatCard
          title="Agency/Contract %"
          value={`${data.agency_contract_percentage.toFixed(1)}%`}
          subtitle={data.agency_contract_percentage > 30 ? "Above target" : "Within target"}
          color={data.agency_contract_percentage > 30 ? "#f59e0b" : undefined}
        />
        <StatCard title="Daily Labor Cost" value={`$${Math.round(data.daily_labor_cost).toLocaleString()}`} />
        <StatCard
          title="Credential Gaps"
          value={data.credential_gaps_count}
          color={data.credential_gaps_count > 0 ? "#ef4444" : undefined}
        />
      </Stack>
    );
  };

  const renderRatiosTab = () => {
    const active = summary;
    const rows = active.data?.items ?? [];
    const total = active.data?.total ?? 0;

    if (active.isError) {
      return <ErrorState message={(active.error as Error).message} onRetry={() => active.refetch()} />;
    }

    return (
      <DataTable<NurseStaffingSummary>
        rows={rows}
        columns={ratioCols}
        total={total}
        loading={active.isLoading || active.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r) => r.unit_id}
        onRowClick={(r) => setSelectedUnit(r)}
        csvFileName="nurse_staffing_ratios"
        height={540}
      />
    );
  };

  const renderOutsourcedTab = () => {
    if (costBreakdown.isLoading) return <LoadingState />;
    if (costBreakdown.isError)
      return <ErrorState message={costBreakdown.error?.message} onRetry={() => costBreakdown.refetch()} />;

    const data = costBreakdown.data;
    if (!data) return <EmptyState title="No data" description="Cost breakdown data is unavailable." />;

    return (
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Labor Cost by Employment Type
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                >
                  {pieData.map((entry, idx) => (
                    <Cell key={idx} fill={EMPLOYMENT_COLORS[entry.name] ?? "#64748b"} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `$${Math.round(value).toLocaleString()}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Box>

          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Breakdown Details
            </Typography>
            <Stack spacing={2}>
              {data.breakdown_by_type.map((item) => (
                <Card key={item.employment_type} variant="outlined">
                  <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {item.employment_type}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {item.nurse_count} nurses • {item.total_hours.toFixed(0)} hours
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: "right" }}>
                        <Typography variant="h6" color={EMPLOYMENT_COLORS[item.employment_type]}>
                          ${Math.round(item.total_cost).toLocaleString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.percentage_of_total.toFixed(1)}% of total
                        </Typography>
                      </Box>
                    </Stack>
                    <Typography variant="caption" color="text.secondary">
                      Avg hourly: ${Math.round(item.avg_hourly_rate)}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>

            <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
              <Stack direction="row" justifyContent="space-between">
                <Typography fontWeight={600}>Internal Staff</Typography>
                <Typography fontWeight={600} color="#3b82f6">
                  {data.internal_percentage.toFixed(1)}%
                </Typography>
              </Stack>
              <Stack direction="row" justifyContent="space-between">
                <Typography fontWeight={600}>Outsourced (Contract + Agency)</Typography>
                <Typography fontWeight={600} color={data.outsourced_percentage > 30 ? "#ef4444" : "#f59e0b"}>
                  {data.outsourced_percentage.toFixed(1)}%
                </Typography>
              </Stack>
            </Box>
          </Box>
        </Stack>
      </Stack>
    );
  };

  const renderCredentialGapsTab = () => {
    const active = credentialGaps;
    const rows = active.data?.items ?? [];
    const total = active.data?.total ?? 0;

    if (active.isError) {
      return <ErrorState message={(active.error as Error).message} onRetry={() => active.refetch()} />;
    }

    return (
      <DataTable<CredentialGapRow>
        rows={rows}
        columns={gapCols}
        total={total}
        loading={active.isLoading || active.isFetching}
        state={tableState}
        onStateChange={onStateChange}
        getRowId={(r) => `${r.unit_id}-${r.required_cred_type}`}
        onRowClick={(r) => setSelectedGap(r)}
        csvFileName="nurse_credential_gaps"
        height={540}
      />
    );
  };

  return (
    <Stack spacing={3}>
      <Typography variant="h5">Nurse Staffing Command Center</Typography>

      {renderKpis()}

      <Tabs
        value={tab}
        onChange={(_, v) => {
          setTab(v);
          setSelectedUnit(null);
          setSelectedGap(null);
          setTableState((s) => ({ ...s, page: 1 }));
        }}
      >
        <Tab value="ratios" label="Ratio Monitor" />
        <Tab value="outsourced" label="Outsourced Staff & Costs" />
        <Tab value="credential_gaps" label="Credential Gaps" />
      </Tabs>

      <FilterBar
        onReset={() => {
          setFacilityId("");
          setUnitType("");
          setStaffingStatus("");
          setGapSeverity("");
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ width: "100%" }}>
          <SearchInput value={facilityId} onChange={setFacilityId} placeholder="Facility ID…" />
          <SearchInput value={unitType} onChange={setUnitType} placeholder="Unit type (ICU, ED, MED_SURG…)" />
          {tab === "ratios" && (
            <SearchInput
              value={staffingStatus}
              onChange={setStaffingStatus}
              placeholder="Status (UNDERSTAFFED,OPTIMAL,OVERSTAFFED)"
            />
          )}
          {tab === "credential_gaps" && (
            <SearchInput value={gapSeverity} onChange={setGapSeverity} placeholder="Severity (LOW,MEDIUM,HIGH,CRITICAL)" />
          )}
        </Stack>
      </FilterBar>

      <Box>
        {tab === "ratios" && renderRatiosTab()}
        {tab === "outsourced" && renderOutsourcedTab()}
        {tab === "credential_gaps" && renderCredentialGapsTab()}
      </Box>

      {/* Unit Detail Side Panel */}
      <SidePanel
        open={Boolean(selectedUnit)}
        onClose={() => setSelectedUnit(null)}
        title={selectedUnit?.unit_name ?? "Unit Detail"}
        subtitle={
          selectedUnit
            ? `${selectedUnit.unit_type} • ${selectedUnit.facility_name ?? selectedUnit.facility_id}`
            : undefined
        }
        width={560}
      >
        {selectedUnit ? (
          <Stack spacing={2}>
            <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
              <Stack direction="row" spacing={2} justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Census
                  </Typography>
                  <Typography variant="h6">{selectedUnit.current_census}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Target Ratio
                  </Typography>
                  <Typography variant="h6">1:{selectedUnit.target_ratio}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Required / Assigned
                  </Typography>
                  <Typography variant="h6">
                    {selectedUnit.nurses_required} / {selectedUnit.nurses_assigned}
                  </Typography>
                </Box>
              </Stack>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Staffing Breakdown
              </Typography>
              <Stack direction="row" spacing={2}>
                <Chip
                  label={`Internal: ${selectedUnit.nurses_internal}`}
                  sx={{ bgcolor: EMPLOYMENT_COLORS.INTERNAL, color: "white" }}
                />
                <Chip
                  label={`Contract: ${selectedUnit.nurses_contract}`}
                  sx={{ bgcolor: EMPLOYMENT_COLORS.CONTRACT, color: "white" }}
                />
                <Chip
                  label={`Agency: ${selectedUnit.nurses_agency}`}
                  sx={{ bgcolor: EMPLOYMENT_COLORS.AGENCY, color: "white" }}
                />
              </Stack>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Assigned Nurses
              </Typography>
              {unitDetail.isLoading ? (
                <LoadingState />
              ) : unitDetail.isError ? (
                <ErrorState message={unitDetail.error?.message} onRetry={() => unitDetail.refetch()} />
              ) : unitDetail.data?.assigned_nurses?.length ? (
                <Stack spacing={1}>
                  {unitDetail.data.assigned_nurses.map((nurse) => (
                    <Box
                      key={nurse.provider_id}
                      sx={{ p: 1.5, border: "1px solid", borderColor: "divider", borderRadius: 2 }}
                    >
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {nurse.provider_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {nurse.employment_type} • ${Math.round(nurse.hourly_rate)}/hr
                          </Typography>
                        </Box>
                        <Chip
                          size="small"
                          label={nurse.is_fully_credentialed ? "Credentialed" : "Missing certs"}
                          color={nurse.is_fully_credentialed ? "success" : "warning"}
                        />
                      </Stack>
                      {nurse.missing_certifications.length > 0 && (
                        <Typography variant="caption" color="error">
                          Missing: {nurse.missing_certifications.join(", ")}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Stack>
              ) : (
                <EmptyState title="No nurses" description="No nurses assigned to this unit." />
              )}
            </Box>

            <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Daily Labor Cost
              </Typography>
              <Typography variant="h5">${Math.round(selectedUnit.labor_cost_daily).toLocaleString()}</Typography>
            </Box>
          </Stack>
        ) : null}
      </SidePanel>

      {/* Credential Gap Side Panel */}
      <SidePanel
        open={Boolean(selectedGap)}
        onClose={() => setSelectedGap(null)}
        title="Credential Gap Detail"
        subtitle={
          selectedGap
            ? `${selectedGap.unit_name} • ${selectedGap.required_cred_type}`
            : undefined
        }
        width={480}
      >
        {selectedGap ? (
          <Stack spacing={2}>
            <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
              <Typography variant="body2">
                <strong>Unit:</strong> {selectedGap.unit_name} ({selectedGap.unit_type})
              </Typography>
              <Typography variant="body2">
                <strong>Facility:</strong> {selectedGap.facility_name ?? selectedGap.facility_id}
              </Typography>
              <Typography variant="body2">
                <strong>Required Certification:</strong> {selectedGap.required_cred_type}
              </Typography>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Gap Analysis
              </Typography>
              <Stack direction="row" spacing={2}>
                <Card variant="outlined" sx={{ flex: 1, textAlign: "center", p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Total Assigned
                  </Typography>
                  <Typography variant="h5">{selectedGap.nurses_assigned}</Typography>
                </Card>
                <Card variant="outlined" sx={{ flex: 1, textAlign: "center", p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    With Cert
                  </Typography>
                  <Typography variant="h5" color="success.main">
                    {selectedGap.nurses_with_cert}
                  </Typography>
                </Card>
                <Card variant="outlined" sx={{ flex: 1, textAlign: "center", p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Missing
                  </Typography>
                  <Typography variant="h5" color="error.main">
                    {selectedGap.nurses_missing_cert}
                  </Typography>
                </Card>
              </Stack>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Severity
              </Typography>
              <Chip
                label={selectedGap.gap_severity}
                sx={{
                  bgcolor:
                    selectedGap.gap_severity === "CRITICAL"
                      ? "#ef4444"
                      : selectedGap.gap_severity === "HIGH"
                      ? "#f97316"
                      : selectedGap.gap_severity === "MEDIUM"
                      ? "#f59e0b"
                      : "#64748b",
                  color: "white",
                  fontWeight: 600
                }}
              />
            </Box>

            {selectedGap.affected_nurse_ids.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Affected Nurses
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedGap.affected_nurse_ids.join(", ")}
                </Typography>
              </Box>
            )}
          </Stack>
        ) : null}
      </SidePanel>
    </Stack>
  );
}
