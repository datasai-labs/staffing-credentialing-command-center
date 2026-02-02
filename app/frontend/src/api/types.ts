import { z } from "zod";

export const PageResponseSchema = <T extends z.ZodTypeAny>(item: T) =>
  z.object({
    items: z.array(item),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive()
  });

export const KpiSummaryDailySchema = z.object({
  kpi_date: z.string(),
  providers_total: z.number(),
  providers_pending: z.number(),
  providers_expiring_30d: z.number(),
  daily_revenue_at_risk_est: z.number(),
  last_built_at: z.string()
});
export type KpiSummaryDaily = z.infer<typeof KpiSummaryDailySchema>;

export const Provider360Schema = z.object({
  provider_id: z.string(),
  provider_name: z.string(),
  specialty: z.string(),
  home_facility_id: z.string(),
  hired_at: z.string(),
  provider_status: z.string(),
  created_at: z.string(),

  home_facility_name: z.string().nullable().optional(),
  state_license_status: z.string().nullable().optional(),
  state_license_days_left: z.number().nullable().optional(),
  acls_status: z.string().nullable().optional(),
  acls_days_left: z.number().nullable().optional(),

  // Use default() without optional() so output type is always number (avoids TS build issues)
  active_privilege_count: z.number().default(0),
  active_privilege_facility_count: z.number().default(0),
  active_payer_count: z.number().default(0),

  last_built_at: z.string().nullable().optional()
});
export type Provider360 = z.infer<typeof Provider360Schema>;

export const ProviderMiniSchema = z.object({
  provider_id: z.string(),
  provider_name: z.string(),
  specialty: z.string().nullable().optional(),
  provider_status: z.string().nullable().optional()
});
export type ProviderMini = z.infer<typeof ProviderMiniSchema>;

export const CredentialRiskRowSchema = z.object({
  event_id: z.string(),
  provider_id: z.string(),
  cred_type: z.string(),
  issued_at: z.string(),
  expires_at: z.string(),
  verified_at: z.string().nullable().optional(),
  source_system: z.string(),
  cred_status: z.string(),
  ingested_at: z.string(),
  days_until_expiration: z.number(),
  risk_bucket: z.string(),
  last_built_at: z.string().nullable().optional()
});
export type CredentialRiskRow = z.infer<typeof CredentialRiskRowSchema>;

export const ProviderDetailResponseSchema = z.object({
  provider: Provider360Schema,
  credential_risk_rows: z.array(CredentialRiskRowSchema)
});
export type ProviderDetailResponse = z.infer<typeof ProviderDetailResponseSchema>;

export const StaffingGapSchema = z.object({
  shift_id: z.string(),
  facility_id: z.string(),
  facility_name: z.string().nullable().optional(),
  start_ts: z.string(),
  end_ts: z.string(),
  required_procedure_code: z.string(),
  procedure_name: z.string().nullable().optional(),
  required_count: z.number(),
  assigned_count: z.number(),
  eligible_provider_count: z.number(),
  gap_count: z.number(),
  risk_reason: z.string(),
  risk_level: z.string(),
  last_built_at: z.string().nullable().optional()
});
export type StaffingGap = z.infer<typeof StaffingGapSchema>;

export const ShiftRecommendationsSchema = z.object({
  shift_id: z.string(),
  recommended_provider_ids: z.array(z.string()),
  recommended_providers: z.array(ProviderMiniSchema).nullable().optional()
});
export type ShiftRecommendations = z.infer<typeof ShiftRecommendationsSchema>;

// ---- Summary endpoints (charts) ----

export const CountByLabelSchema = z.object({
  label: z.string(),
  count: z.number()
});
export type CountByLabel = z.infer<typeof CountByLabelSchema>;

export const DateValueSchema = z.object({
  date: z.string(),
  value: z.number()
});
export type DateValue = z.infer<typeof DateValueSchema>;

export const DateCountSchema = z.object({
  date: z.string(),
  count: z.number()
});
export type DateCount = z.infer<typeof DateCountSchema>;

export const KpiTrendPointSchema = z.object({
  kpi_date: z.string(),
  providers_pending: z.number(),
  providers_expiring_30d: z.number(),
  daily_revenue_at_risk_est: z.number()
});
export type KpiTrendPoint = z.infer<typeof KpiTrendPointSchema>;

export const KpiTrendResponseSchema = z.object({
  days: z.number(),
  points: z.array(KpiTrendPointSchema)
});
export type KpiTrendResponse = z.infer<typeof KpiTrendResponseSchema>;

export const StaffingSummaryResponseSchema = z.object({
  by_risk_level: z.array(CountByLabelSchema),
  daily_gap_count: z.array(DateValueSchema),
  top_facilities: z.array(z.record(z.any())),
  top_procedures: z.array(z.record(z.any()))
});
export type StaffingSummaryResponse = z.infer<typeof StaffingSummaryResponseSchema>;

export const CredentialRiskSummaryResponseSchema = z.object({
  by_bucket: z.array(CountByLabelSchema),
  by_cred_type: z.array(CountByLabelSchema),
  expires_by_week: z.array(DateCountSchema)
});
export type CredentialRiskSummaryResponse = z.infer<typeof CredentialRiskSummaryResponseSchema>;

export const ProvidersSummaryResponseSchema = z.object({
  by_specialty: z.array(CountByLabelSchema),
  expiring_funnel: z.array(CountByLabelSchema),
  readiness_histogram: z.array(CountByLabelSchema)
});
export type ProvidersSummaryResponse = z.infer<typeof ProvidersSummaryResponseSchema>;

export const ShiftPredictionResponseSchema = z.object({
  shift_id: z.string(),
  predicted_gap_prob: z.number().nullable().optional(),
  predicted_is_gap: z.number().nullable().optional(),
  scored_at: z.string().nullable().optional()
});
export type ShiftPredictionResponse = z.infer<typeof ShiftPredictionResponseSchema>;

// ---- Actions (closed-loop workflow) ----

export const RiskActionSchema = z.object({
  action_id: z.string(),
  entity_type: z.enum(["SHIFT", "PROVIDER"]),
  entity_id: z.string(),
  facility_id: z.string().nullable().optional(),
  action_type: z.string(),
  status: z.enum(["OPEN", "IN_PROGRESS", "RESOLVED"]),
  priority: z.enum(["LOW", "MEDIUM", "HIGH"]).default("MEDIUM"),
  owner: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  resolved_at: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  last_built_at: z.string().nullable().optional()
});
export type RiskAction = z.infer<typeof RiskActionSchema>;

export const ActionsSummarySchema = z.object({
  open_count: z.number(),
  in_progress_count: z.number(),
  resolved_count: z.number(),
  median_time_to_resolve_hours: z.number().nullable().optional()
});
export type ActionsSummary = z.infer<typeof ActionsSummarySchema>;