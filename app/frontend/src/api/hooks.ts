import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { apiGet, apiPatch, apiPost, toQuery } from "./client";
import {
  ActionsSummarySchema, CostBreakdownSchema, CredentialGapRowSchema, CredentialRiskRowSchema,
  CredentialRiskSummaryResponseSchema, CredentialExpiringRowSchema, KpiSummaryDailySchema,
  KpiTrendResponseSchema, NurseStaffingKpisSchema, NurseStaffingSummarySchema, PageResponseSchema,
  ProviderBlockersRowSchema, Provider360Schema, ProviderDetailResponseSchema, ProvidersSummaryResponseSchema,
  RiskActionSchema, ScenarioCoverageResponseSchema, ShiftRecommendationsSchema,
  ShiftEligibilityExplainResponseSchema, ShiftPredictionResponseSchema, StaffingGapSchema,
  StaffingSummaryResponseSchema, UnitDetailSchema, CreateRiskActionRequestSchema, UpdateRiskActionRequestSchema
} from "./types";

function parse<S extends z.ZodTypeAny>(schema: S, data: unknown): z.infer<S> {
  const res = schema.safeParse(data);
  if (!res.success) throw new Error(`Validation failed: ${res.error.message}`);
  return res.data;
}

type QueryOpts = { enabled?: boolean; keepPrevious?: boolean };

function useGet<S extends z.ZodTypeAny>(key: unknown[], url: string, schema: S, opts: QueryOpts = {}) {
  return useQuery<z.infer<S>, Error>({
    queryKey: key,
    queryFn: async ({ signal }) => parse(schema, await apiGet<unknown>(url, signal)),
    enabled: opts.enabled,
    placeholderData: opts.keepPrevious ? keepPreviousData : undefined
  });
}

function usePaged<S extends z.ZodTypeAny>(key: string, url: string, schema: S, params: Record<string, unknown>) {
  return useGet([key, params], `${url}${toQuery(params)}`, PageResponseSchema(schema), { keepPrevious: true });
}

// ─────────────────────────────────────────────────────────────────────────────
// KPIs
// ─────────────────────────────────────────────────────────────────────────────

export const useKpis = (asOfDate?: string) =>
  useGet(["kpis", asOfDate ?? "latest"], `/api/v1/kpis${toQuery({ as_of_date: asOfDate })}`, KpiSummaryDailySchema);

export const useKpisTrend = (days = 30) =>
  useGet(["kpis_trend", days], `/api/v1/kpis/trend${toQuery({ days })}`, KpiTrendResponseSchema);

// ─────────────────────────────────────────────────────────────────────────────
// Providers
// ─────────────────────────────────────────────────────────────────────────────

export const useProviders = (params: { q?: string; specialty?: string; status?: string; expiring_within_days?: number; page: number; page_size: number; sort?: string }) =>
  usePaged("providers", "/api/v1/providers", Provider360Schema, params);

export const useProvider = (providerId: string) =>
  useGet(["provider", providerId], `/api/v1/providers/${providerId}`, ProviderDetailResponseSchema, { enabled: Boolean(providerId) });

export const useProvidersSummary = (params: { specialty?: string; status?: string; expiring_within_days?: number }) =>
  useGet(["providers_summary", params], `/api/v1/providers/summary${toQuery(params)}`, ProvidersSummaryResponseSchema);

// ─────────────────────────────────────────────────────────────────────────────
// Staffing Gaps
// ─────────────────────────────────────────────────────────────────────────────

export const useStaffingGaps = (params: { start_date?: string; end_date?: string; facility_id?: string; risk_level?: string; procedure_code?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("staffing_gaps", "/api/v1/staffing_gaps", StaffingGapSchema, params);

export const useStaffingSummary = (params: { start_date?: string; end_date?: string; facility_id?: string; risk_level?: string; procedure_code?: string }) =>
  useGet(["staffing_summary", params], `/api/v1/staffing_gaps/summary${toQuery(params)}`, StaffingSummaryResponseSchema);

export const useShiftRecommendations = (shiftId?: string, includeProviders = true) =>
  useGet(["shift_recs", shiftId, includeProviders], `/api/v1/shifts/${shiftId}/recommendations${toQuery({ include_providers: includeProviders })}`, ShiftRecommendationsSchema, { enabled: Boolean(shiftId) });

export const useShiftPrediction = (shiftId?: string) =>
  useGet(["shift_prediction", shiftId], `/api/v1/shifts/${shiftId}/prediction`, ShiftPredictionResponseSchema, { enabled: Boolean(shiftId) });

export const useShiftEligibilityExplain = (shiftId?: string) =>
  useGet(["shift_eligibility_explain", shiftId], `/api/v1/shifts/${shiftId}/eligibility_explain`, ShiftEligibilityExplainResponseSchema, { enabled: Boolean(shiftId) });

// ─────────────────────────────────────────────────────────────────────────────
// Credential Risk
// ─────────────────────────────────────────────────────────────────────────────

export const useCredentialRisk = (params: { provider_id?: string; cred_type?: string; risk_bucket?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("credential_risk", "/api/v1/credential_risk", CredentialRiskRowSchema, params);

export const useCredentialRiskSummary = (params: { cred_type?: string; risk_bucket?: string }) =>
  useGet(["credential_risk_summary", params], `/api/v1/credential_risk/summary${toQuery(params)}`, CredentialRiskSummaryResponseSchema);

// ─────────────────────────────────────────────────────────────────────────────
// Worklists
// ─────────────────────────────────────────────────────────────────────────────

export const useWorklistNoEligibleShifts = (params: { start_date?: string; end_date?: string; facility_id?: string; risk_level?: string; procedure_code?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("worklist_no_eligible_shifts", "/api/v1/worklists/shifts/no_eligible", StaffingGapSchema, params);

export const useWorklistExpiringCredentials = (params: { provider_id?: string; specialty?: string; facility_id?: string; cred_type?: string; risk_bucket?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("worklist_expiring_credentials", "/api/v1/worklists/credentials/expiring", CredentialExpiringRowSchema, params);

export const useWorklistProviderBlockers = (params: { facility_id?: string; specialty?: string; blocker?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("worklist_provider_blockers", "/api/v1/worklists/providers/blockers", ProviderBlockersRowSchema, params);

// ─────────────────────────────────────────────────────────────────────────────
// Actions
// ─────────────────────────────────────────────────────────────────────────────

export const useActions = (params: { entity_type?: "SHIFT" | "PROVIDER"; entity_id?: string; status?: "OPEN" | "IN_PROGRESS" | "RESOLVED"; action_type?: string; facility_id?: string; page: number; page_size: number; sort?: string }) =>
  usePaged("actions", "/api/v1/actions", RiskActionSchema, params);

export const useActionsSummary = (params: { facility_id?: string } = {}) =>
  useGet(["actions_summary", params], `/api/v1/actions/summary${toQuery(params)}`, ActionsSummarySchema);

export function useCreateAction() {
  const qc = useQueryClient();
  return useMutation<z.infer<typeof RiskActionSchema>, Error, z.infer<typeof CreateRiskActionRequestSchema>>({
    mutationFn: async (payload) => parse(RiskActionSchema, await apiPost<unknown>("/api/v1/actions", payload)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["actions"] }); qc.invalidateQueries({ queryKey: ["actions_summary"] }); }
  });
}

export function useUpdateAction() {
  const qc = useQueryClient();
  return useMutation<z.infer<typeof RiskActionSchema>, Error, { action_id: string; patch: z.infer<typeof UpdateRiskActionRequestSchema> }>({
    mutationFn: async ({ action_id, patch }) => parse(RiskActionSchema, await apiPatch<unknown>(`/api/v1/actions/${action_id}`, patch)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["actions"] }); qc.invalidateQueries({ queryKey: ["actions_summary"] }); }
  });
}

export function useScenarioCoverage() {
  return useMutation<z.infer<typeof ScenarioCoverageResponseSchema>, Error, { shift_ids: string[]; assumptions?: Record<string, string[]> }>({
    mutationFn: async (payload) => parse(ScenarioCoverageResponseSchema, await apiPost<unknown>("/api/v1/scenario/coverage", payload))
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Nurse Staffing
// ─────────────────────────────────────────────────────────────────────────────

export const useNurseStaffingKpis = (params: { facility_id?: string; kpi_date?: string } = {}) =>
  useGet(["nurse_staffing_kpis", params], `/api/v1/nurse_staffing/kpis${toQuery(params)}`, NurseStaffingKpisSchema);

export const useNurseStaffingSummary = (params: { facility_id?: string; unit_type?: string; staffing_status?: string; summary_date?: string; page: number; page_size: number }) =>
  usePaged("nurse_staffing_summary", "/api/v1/nurse_staffing/summary", NurseStaffingSummarySchema, params);

export const useUnitDetail = (unitId?: string) =>
  useGet(["unit_detail", unitId], `/api/v1/nurse_staffing/units/${unitId}`, UnitDetailSchema, { enabled: Boolean(unitId) });

export const useCredentialGaps = (params: { facility_id?: string; unit_type?: string; gap_severity?: string; page: number; page_size: number }) =>
  usePaged("credential_gaps", "/api/v1/nurse_staffing/credential_gaps", CredentialGapRowSchema, params);

export const useCostBreakdown = (params: { facility_id?: string; start_date?: string; end_date?: string } = {}) =>
  useGet(["cost_breakdown", params], `/api/v1/nurse_staffing/cost_breakdown${toQuery(params)}`, CostBreakdownSchema);
