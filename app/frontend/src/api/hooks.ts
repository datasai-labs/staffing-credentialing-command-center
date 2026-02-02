import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";

import { apiGet, apiPatch, apiPost, toQuery } from "./client";
import {
  ActionsSummarySchema,
  CostBreakdownSchema,
  CreateRiskActionRequestSchema,
  CredentialGapRowSchema,
  CredentialRiskRowSchema,
  CredentialRiskSummaryResponseSchema,
  CredentialExpiringRowSchema,
  KpiSummaryDailySchema,
  KpiTrendResponseSchema,
  NurseStaffingKpisSchema,
  NurseStaffingSummarySchema,
  PageResponseSchema,
  ProviderBlockersRowSchema,
  Provider360Schema,
  ProviderDetailResponseSchema,
  ProvidersSummaryResponseSchema,
  RiskActionSchema,
  ScenarioCoverageRequestSchema,
  ScenarioCoverageResponseSchema,
  ShiftRecommendationsSchema,
  ShiftEligibilityExplainResponseSchema,
  ShiftPredictionResponseSchema,
  StaffingGapSchema,
  StaffingSummaryResponseSchema,
  UnitDetailSchema,
  UpdateRiskActionRequestSchema
} from "./types";

function parseOrThrow<S extends z.ZodTypeAny>(schema: S, data: unknown): z.infer<S> {
  const res = schema.safeParse(data);
  if (!res.success) {
    throw new Error(`Response validation failed: ${res.error.message}`);
  }
  // safeParse returns the schema *output* type (defaults/transforms applied)
  return res.data as z.infer<S>;
}

export function useKpis(asOfDate?: string) {
  type Resp = z.infer<typeof KpiSummaryDailySchema>;
  return useQuery<Resp, Error>({
    queryKey: ["kpis", asOfDate ?? "latest"],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/kpis${toQuery({ as_of_date: asOfDate })}`, signal);
      return parseOrThrow(KpiSummaryDailySchema, data);
    }
  });
}

export function useKpisTrend(days = 30) {
  type Resp = z.infer<typeof KpiTrendResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["kpis_trend", days],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/kpis/trend${toQuery({ days })}`, signal);
      return parseOrThrow(KpiTrendResponseSchema, data);
    }
  });
}

export function useProviders(params: {
  q?: string;
  specialty?: string;
  status?: string;
  expiring_within_days?: number;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(Provider360Schema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["providers", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/providers${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useProvider(providerId: string) {
  type Resp = z.infer<typeof ProviderDetailResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["provider", providerId],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/providers/${providerId}`, signal);
      return parseOrThrow(ProviderDetailResponseSchema, data);
    },
    enabled: Boolean(providerId)
  });
}

export function useStaffingGaps(params: {
  start_date?: string;
  end_date?: string;
  facility_id?: string;
  risk_level?: string;
  procedure_code?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(StaffingGapSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["staffing_gaps", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/staffing_gaps${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useStaffingSummary(params: {
  start_date?: string;
  end_date?: string;
  facility_id?: string;
  risk_level?: string;
  procedure_code?: string;
}) {
  type Resp = z.infer<typeof StaffingSummaryResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["staffing_summary", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/staffing_gaps/summary${toQuery(params)}`, signal);
      return parseOrThrow(StaffingSummaryResponseSchema, data);
    }
  });
}

export function useShiftRecommendations(shiftId?: string, includeProviders = true) {
  type Resp = z.infer<typeof ShiftRecommendationsSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["shift_recs", shiftId, includeProviders],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(
        `/api/v1/shifts/${shiftId}/recommendations${toQuery({ include_providers: includeProviders })}`,
        signal
      );
      return parseOrThrow(ShiftRecommendationsSchema, data);
    },
    enabled: Boolean(shiftId)
  });
}

export function useShiftPrediction(shiftId?: string) {
  type Resp = z.infer<typeof ShiftPredictionResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["shift_prediction", shiftId],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/shifts/${shiftId}/prediction`, signal);
      return parseOrThrow(ShiftPredictionResponseSchema, data);
    },
    enabled: Boolean(shiftId)
  });
}

export function useShiftEligibilityExplain(shiftId?: string) {
  type Resp = z.infer<typeof ShiftEligibilityExplainResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["shift_eligibility_explain", shiftId],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/shifts/${shiftId}/eligibility_explain`, signal);
      return parseOrThrow(ShiftEligibilityExplainResponseSchema, data);
    },
    enabled: Boolean(shiftId)
  });
}

export function useCredentialRisk(params: {
  provider_id?: string;
  cred_type?: string;
  risk_bucket?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(CredentialRiskRowSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["credential_risk", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/credential_risk${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useCredentialRiskSummary(params: { cred_type?: string; risk_bucket?: string }) {
  type Resp = z.infer<typeof CredentialRiskSummaryResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["credential_risk_summary", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/credential_risk/summary${toQuery(params)}`, signal);
      return parseOrThrow(CredentialRiskSummaryResponseSchema, data);
    }
  });
}

export function useWorklistNoEligibleShifts(params: {
  start_date?: string;
  end_date?: string;
  facility_id?: string;
  risk_level?: string;
  procedure_code?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(StaffingGapSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["worklist_no_eligible_shifts", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/worklists/shifts/no_eligible${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useWorklistExpiringCredentials(params: {
  provider_id?: string;
  specialty?: string;
  facility_id?: string;
  cred_type?: string;
  risk_bucket?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(CredentialExpiringRowSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["worklist_expiring_credentials", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/worklists/credentials/expiring${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useWorklistProviderBlockers(params: {
  facility_id?: string;
  specialty?: string;
  blocker?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(ProviderBlockersRowSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["worklist_provider_blockers", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/worklists/providers/blockers${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useProvidersSummary(params: { specialty?: string; status?: string; expiring_within_days?: number }) {
  type Resp = z.infer<typeof ProvidersSummaryResponseSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["providers_summary", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/providers/summary${toQuery(params)}`, signal);
      return parseOrThrow(ProvidersSummaryResponseSchema, data);
    }
  });
}

export function useActions(params: {
  entity_type?: "SHIFT" | "PROVIDER";
  entity_id?: string;
  status?: "OPEN" | "IN_PROGRESS" | "RESOLVED";
  action_type?: string;
  facility_id?: string;
  page: number;
  page_size: number;
  sort?: string;
}) {
  const schema = PageResponseSchema(RiskActionSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["actions", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/actions${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useActionsSummary(params: { facility_id?: string } = {}) {
  type Resp = z.infer<typeof ActionsSummarySchema>;
  return useQuery<Resp, Error>({
    queryKey: ["actions_summary", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/actions/summary${toQuery(params)}`, signal);
      return parseOrThrow(ActionsSummarySchema, data);
    }
  });
}

export function useCreateAction() {
  const qc = useQueryClient();
  type Resp = z.infer<typeof RiskActionSchema>;
  type Req = z.infer<typeof CreateRiskActionRequestSchema>;
  return useMutation<Resp, Error, Req>({
    mutationFn: async (payload: Req) => {
      const data = await apiPost<unknown>(`/api/v1/actions`, payload);
      return parseOrThrow(RiskActionSchema, data);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["actions"] });
      await qc.invalidateQueries({ queryKey: ["actions_summary"] });
    }
  });
}

export function useUpdateAction() {
  const qc = useQueryClient();
  type Resp = z.infer<typeof RiskActionSchema>;
  type Patch = z.infer<typeof UpdateRiskActionRequestSchema>;
  return useMutation<Resp, Error, { action_id: string; patch: Patch }>({
    mutationFn: async ({ action_id, patch }: { action_id: string; patch: Patch }) => {
      const data = await apiPatch<unknown>(`/api/v1/actions/${action_id}`, patch);
      return parseOrThrow(RiskActionSchema, data);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["actions"] });
      await qc.invalidateQueries({ queryKey: ["actions_summary"] });
    }
  });
}

export function useScenarioCoverage() {
  type Req = z.infer<typeof ScenarioCoverageRequestSchema>;
  type Resp = z.infer<typeof ScenarioCoverageResponseSchema>;
  return useMutation<Resp, Error, Req>({
    mutationFn: async (payload: Req) => {
      const data = await apiPost<unknown>(`/api/v1/scenario/coverage`, payload);
      return parseOrThrow(ScenarioCoverageResponseSchema, data);
    }
  });
}

// ---- Nurse Staffing Optimization ----

export function useNurseStaffingKpis(params: { facility_id?: string; kpi_date?: string } = {}) {
  type Resp = z.infer<typeof NurseStaffingKpisSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["nurse_staffing_kpis", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/nurse_staffing/kpis${toQuery(params)}`, signal);
      return parseOrThrow(NurseStaffingKpisSchema, data);
    }
  });
}

export function useNurseStaffingSummary(params: {
  facility_id?: string;
  unit_type?: string;
  staffing_status?: string;
  summary_date?: string;
  page: number;
  page_size: number;
}) {
  const schema = PageResponseSchema(NurseStaffingSummarySchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["nurse_staffing_summary", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/nurse_staffing/summary${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useUnitDetail(unitId?: string) {
  type Resp = z.infer<typeof UnitDetailSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["unit_detail", unitId],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/nurse_staffing/units/${unitId}`, signal);
      return parseOrThrow(UnitDetailSchema, data);
    },
    enabled: Boolean(unitId)
  });
}

export function useCredentialGaps(params: {
  facility_id?: string;
  unit_type?: string;
  gap_severity?: string;
  page: number;
  page_size: number;
}) {
  const schema = PageResponseSchema(CredentialGapRowSchema);
  type Resp = z.infer<typeof schema>;
  return useQuery<Resp, Error>({
    queryKey: ["credential_gaps", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/nurse_staffing/credential_gaps${toQuery(params)}`, signal);
      return parseOrThrow(schema, data);
    },
    placeholderData: keepPreviousData
  });
}

export function useCostBreakdown(params: { facility_id?: string; start_date?: string; end_date?: string } = {}) {
  type Resp = z.infer<typeof CostBreakdownSchema>;
  return useQuery<Resp, Error>({
    queryKey: ["cost_breakdown", params],
    queryFn: async ({ signal }) => {
      const data = await apiGet<unknown>(`/api/v1/nurse_staffing/cost_breakdown${toQuery(params)}`, signal);
      return parseOrThrow(CostBreakdownSchema, data);
    }
  });
}
