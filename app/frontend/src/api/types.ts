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

// ---- Worklists + eligibility + scenarios (derived) ----

export const CredentialExpiringRowSchema = CredentialRiskRowSchema.extend({
  provider_name: z.string().nullable().optional(),
  specialty: z.string().nullable().optional(),
  home_facility_id: z.string().nullable().optional(),
  home_facility_name: z.string().nullable().optional()
});
export type CredentialExpiringRow = z.infer<typeof CredentialExpiringRowSchema>;

export const ProviderBlockersRowSchema = z.object({
  provider_id: z.string(),
  provider_name: z.string(),
  specialty: z.string(),
  provider_status: z.string(),
  home_facility_id: z.string(),

  home_facility_name: z.string().nullable().optional(),
  state_license_status: z.string().nullable().optional(),
  state_license_days_left: z.number().nullable().optional(),
  acls_status: z.string().nullable().optional(),
  acls_days_left: z.number().nullable().optional(),
  active_privilege_count: z.number().default(0),
  active_privilege_facility_count: z.number().default(0),
  active_payer_count: z.number().default(0),
  last_built_at: z.string().nullable().optional(),

  blockers: z.array(z.string()).default([]),
  time_to_ready_days: z.number().nullable().optional(),
  time_to_ready_reason: z.string().nullable().optional()
});
export type ProviderBlockersRow = z.infer<typeof ProviderBlockersRowSchema>;

export const EligibilityProviderExplainSchema = z.object({
  provider_id: z.string(),
  provider_name: z.string().nullable().optional(),
  specialty: z.string().nullable().optional(),
  provider_status: z.string().nullable().optional(),
  home_facility_id: z.string().nullable().optional(),
  home_facility_name: z.string().nullable().optional(),
  state_license_status: z.string().nullable().optional(),
  state_license_days_left: z.number().nullable().optional(),
  acls_status: z.string().nullable().optional(),
  acls_days_left: z.number().nullable().optional(),
  active_privilege_count: z.number().nullable().optional(),
  active_payer_count: z.number().nullable().optional(),
  is_eligible: z.boolean(),
  why_eligible: z.array(z.string()),
  why_not: z.array(z.string()),
  time_to_ready_days: z.number().nullable().optional()
});
export type EligibilityProviderExplain = z.infer<typeof EligibilityProviderExplainSchema>;

export const ShiftEligibilityExplainResponseSchema = z.object({
  shift_id: z.string(),
  recommended_provider_ids: z.array(z.string()),
  providers: z.array(EligibilityProviderExplainSchema)
});
export type ShiftEligibilityExplainResponse = z.infer<typeof ShiftEligibilityExplainResponseSchema>;

export const ScenarioAssumptionsSchema = z.object({
  fix_acls_for_provider_ids: z.array(z.string()).default([]),
  fix_license_for_provider_ids: z.array(z.string()).default([]),
  assume_payer_for_provider_ids: z.array(z.string()).default([]),
  assume_privilege_for_provider_ids: z.array(z.string()).default([])
});
export type ScenarioAssumptions = z.infer<typeof ScenarioAssumptionsSchema>;

export const ScenarioCoverageRequestSchema = z.object({
  shift_ids: z.array(z.string()).min(1).max(200),
  assumptions: ScenarioAssumptionsSchema.default({
    fix_acls_for_provider_ids: [],
    fix_license_for_provider_ids: [],
    assume_payer_for_provider_ids: [],
    assume_privilege_for_provider_ids: []
  })
});
export type ScenarioCoverageRequest = z.infer<typeof ScenarioCoverageRequestSchema>;

export const ScenarioShiftResultSchema = z.object({
  shift_id: z.string(),
  baseline_coverable: z.boolean(),
  scenario_coverable: z.boolean(),
  delta_coverable: z.boolean(),
  baseline_best_provider_id: z.string().nullable().optional(),
  scenario_best_provider_id: z.string().nullable().optional(),
  scenario_changes: z.array(z.string()).default([])
});
export type ScenarioShiftResult = z.infer<typeof ScenarioShiftResultSchema>;

export const ScenarioCoverageResponseSchema = z.object({
  shift_count: z.number(),
  baseline_coverable_count: z.number(),
  scenario_coverable_count: z.number(),
  delta_coverable_count: z.number(),
  results: z.array(ScenarioShiftResultSchema)
});
export type ScenarioCoverageResponse = z.infer<typeof ScenarioCoverageResponseSchema>;

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

export const CreateRiskActionRequestSchema = z.object({
  entity_type: z.enum(["SHIFT", "PROVIDER"]),
  entity_id: z.string(),
  facility_id: z.string().nullable().optional(),
  action_type: z.enum(["OUTREACH", "CREDENTIAL_EXPEDITE", "PRIVILEGE_REQUEST", "PAYER_ENROLLMENT_FOLLOWUP"]),
  priority: z.enum(["LOW", "MEDIUM", "HIGH"]).default("MEDIUM"),
  owner: z.string().nullable().optional(),
  notes: z.string().nullable().optional()
});
export type CreateRiskActionRequest = z.infer<typeof CreateRiskActionRequestSchema>;

export const UpdateRiskActionRequestSchema = z.object({
  status: z.enum(["OPEN", "IN_PROGRESS", "RESOLVED"]).optional(),
  priority: z.enum(["LOW", "MEDIUM", "HIGH"]).optional(),
  owner: z.string().nullable().optional(),
  notes: z.string().nullable().optional()
});
export type UpdateRiskActionRequest = z.infer<typeof UpdateRiskActionRequestSchema>;

export const ActionsSummarySchema = z.object({
  open_count: z.number(),
  in_progress_count: z.number(),
  resolved_count: z.number(),
  median_time_to_resolve_hours: z.number().nullable().optional()
});
export type ActionsSummary = z.infer<typeof ActionsSummarySchema>;

// ---- Nurse Staffing Optimization ----

export const EmploymentTypeSchema = z.enum(["INTERNAL", "CONTRACT", "AGENCY"]);
export type EmploymentType = z.infer<typeof EmploymentTypeSchema>;

export const UnitTypeSchema = z.enum(["ICU", "STEP_DOWN", "MED_SURG", "TELEMETRY", "ED", "OR", "L_AND_D", "PSYCH", "NICU", "PACU"]);
export type UnitType = z.infer<typeof UnitTypeSchema>;

export const StaffingStatusSchema = z.enum(["UNDERSTAFFED", "OPTIMAL", "OVERSTAFFED"]);
export type StaffingStatus = z.infer<typeof StaffingStatusSchema>;

export const UnitSchema = z.object({
  unit_id: z.string(),
  facility_id: z.string(),
  facility_name: z.string().nullable().optional(),
  unit_name: z.string(),
  unit_type: z.string(),
  bed_count: z.number(),
  target_ratio: z.number()
});
export type Unit = z.infer<typeof UnitSchema>;

export const NurseStaffingSummarySchema = z.object({
  summary_date: z.string(),
  unit_id: z.string(),
  facility_id: z.string(),
  facility_name: z.string().nullable().optional(),
  unit_name: z.string(),
  unit_type: z.string(),
  bed_count: z.number(),
  current_census: z.number(),
  target_ratio: z.number(),
  nurses_required: z.number(),
  nurses_assigned: z.number(),
  nurses_internal: z.number(),
  nurses_contract: z.number(),
  nurses_agency: z.number(),
  staffing_delta: z.number(),
  staffing_status: z.string(),
  labor_cost_daily: z.number(),
  last_built_at: z.string().nullable().optional()
});
export type NurseStaffingSummary = z.infer<typeof NurseStaffingSummarySchema>;

export const NurseAssignmentSchema = z.object({
  provider_id: z.string(),
  provider_name: z.string(),
  employment_type: z.string(),
  hourly_rate: z.number(),
  shift_start: z.string(),
  shift_end: z.string(),
  certifications: z.array(z.string()).default([]),
  missing_certifications: z.array(z.string()).default([]),
  is_fully_credentialed: z.boolean()
});
export type NurseAssignment = z.infer<typeof NurseAssignmentSchema>;

export const UnitDetailSchema = z.object({
  unit: UnitSchema,
  summary: NurseStaffingSummarySchema,
  assigned_nurses: z.array(NurseAssignmentSchema).default([]),
  required_certifications: z.array(z.string()).default([])
});
export type UnitDetail = z.infer<typeof UnitDetailSchema>;

export const CredentialGapRowSchema = z.object({
  unit_id: z.string(),
  facility_id: z.string(),
  facility_name: z.string().nullable().optional(),
  unit_name: z.string(),
  unit_type: z.string(),
  required_cred_type: z.string(),
  nurses_assigned: z.number(),
  nurses_with_cert: z.number(),
  nurses_missing_cert: z.number(),
  gap_severity: z.string(),
  affected_nurse_ids: z.array(z.string()).default([])
});
export type CredentialGapRow = z.infer<typeof CredentialGapRowSchema>;

export const CostBreakdownItemSchema = z.object({
  employment_type: z.string(),
  nurse_count: z.number(),
  total_hours: z.number(),
  total_cost: z.number(),
  avg_hourly_rate: z.number(),
  percentage_of_total: z.number()
});
export type CostBreakdownItem = z.infer<typeof CostBreakdownItemSchema>;

export const CostBreakdownSchema = z.object({
  facility_id: z.string().nullable().optional(),
  facility_name: z.string().nullable().optional(),
  start_date: z.string(),
  end_date: z.string(),
  total_labor_cost: z.number(),
  breakdown_by_type: z.array(CostBreakdownItemSchema).default([]),
  internal_percentage: z.number(),
  outsourced_percentage: z.number()
});
export type CostBreakdown = z.infer<typeof CostBreakdownSchema>;

export const NurseStaffingKpisSchema = z.object({
  kpi_date: z.string(),
  total_nurses_on_shift: z.number(),
  units_understaffed: z.number(),
  units_optimal: z.number(),
  units_overstaffed: z.number(),
  agency_contract_percentage: z.number(),
  daily_labor_cost: z.number(),
  credential_gaps_count: z.number(),
  last_built_at: z.string().nullable().optional()
});
export type NurseStaffingKpis = z.infer<typeof NurseStaffingKpisSchema>;