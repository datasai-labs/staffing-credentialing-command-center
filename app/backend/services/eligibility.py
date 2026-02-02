from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from models.eligibility import EligibilityProviderExplain


@dataclass(frozen=True)
class Assumptions:
    fix_license_for_provider_ids: set[str]
    fix_acls_for_provider_ids: set[str]
    assume_payer_for_provider_ids: set[str]
    assume_privilege_for_provider_ids: set[str]

    @staticmethod
    def empty() -> "Assumptions":
        return Assumptions(set(), set(), set(), set())


def _get_int(row: dict[str, Any], key: str) -> Optional[int]:
    v = row.get(key)
    if v is None:
        return None
    try:
        return int(v)
    except Exception:  # noqa: BLE001
        return None


def _get_str(row: dict[str, Any], key: str) -> Optional[str]:
    v = row.get(key)
    if v is None:
        return None
    return str(v)


def explain_provider_readiness(row: dict[str, Any], *, assumptions: Assumptions = Assumptions.empty()) -> EligibilityProviderExplain:
    """
    Convert a provider_360_flat row into an explainable eligibility decision.

    This is intentionally simple and demo-friendly (transparent, deterministic, and derived only).
    """
    pid = _get_str(row, "provider_id") or ""
    status = _get_str(row, "provider_status")
    lic_days = _get_int(row, "state_license_days_left")
    acls_days = _get_int(row, "acls_days_left")
    priv_count = _get_int(row, "active_privilege_count")
    payer_count = _get_int(row, "active_payer_count")

    why_ok: list[str] = []
    why_not: list[str] = []

    # Status gate
    if status == "ACTIVE":
        why_ok.append("Provider status is ACTIVE")
        status_ok = True
    else:
        status_ok = False
        why_not.append(f"Provider status is {status or 'UNKNOWN'}")

    # License
    lic_assumed = pid in assumptions.fix_license_for_provider_ids
    if lic_assumed:
        lic_ok = True
        why_ok.append("License assumed renewed (scenario)")
    else:
        if lic_days is None:
            lic_ok = False
            why_not.append("License expiry unknown")
        elif lic_days >= 0:
            lic_ok = True
            why_ok.append(f"License valid (days left: {lic_days})")
        else:
            lic_ok = False
            why_not.append(f"License expired (days overdue: {abs(lic_days)})")

    # ACLS
    acls_assumed = pid in assumptions.fix_acls_for_provider_ids
    if acls_assumed:
        acls_ok = True
        why_ok.append("ACLS assumed renewed (scenario)")
    else:
        if acls_days is None:
            acls_ok = False
            why_not.append("ACLS expiry unknown")
        elif acls_days >= 0:
            acls_ok = True
            why_ok.append(f"ACLS valid (days left: {acls_days})")
        else:
            acls_ok = False
            why_not.append(f"ACLS expired (days overdue: {abs(acls_days)})")

    # Privileges
    priv_assumed = pid in assumptions.assume_privilege_for_provider_ids
    if priv_assumed:
        priv_ok = True
        why_ok.append("Privileges assumed granted (scenario)")
    else:
        priv_ok = (priv_count or 0) > 0
        if priv_ok:
            why_ok.append(f"Privileges active (count: {int(priv_count or 0)})")
        else:
            why_not.append("No active privileges")

    # Payer enrollment
    payer_assumed = pid in assumptions.assume_payer_for_provider_ids
    if payer_assumed:
        payer_ok = True
        why_ok.append("Payer enrollment assumed complete (scenario)")
    else:
        payer_ok = (payer_count or 0) > 0
        if payer_ok:
            why_ok.append(f"Payer enrollments active (count: {int(payer_count or 0)})")
        else:
            why_not.append("No active payer enrollments")

    is_eligible = bool(status_ok and lic_ok and acls_ok and priv_ok and payer_ok)

    # Time-to-ready proxy (days): max of the blocking estimates
    ttr_candidates: list[int] = []
    if not status_ok:
        time_to_ready = None
    else:
        if not lic_ok and not lic_assumed:
            if lic_days is not None and lic_days < 0:
                ttr_candidates.append(abs(lic_days))
            else:
                ttr_candidates.append(30)
        if not acls_ok and not acls_assumed:
            if acls_days is not None and acls_days < 0:
                ttr_candidates.append(abs(acls_days))
            else:
                ttr_candidates.append(14)
        if not priv_ok and not priv_assumed:
            ttr_candidates.append(14)
        if not payer_ok and not payer_assumed:
            ttr_candidates.append(45)
        time_to_ready = max(ttr_candidates) if ttr_candidates else 0

    return EligibilityProviderExplain(
        provider_id=pid,
        provider_name=_get_str(row, "provider_name"),
        specialty=_get_str(row, "specialty"),
        provider_status=status,
        home_facility_id=_get_str(row, "home_facility_id"),
        home_facility_name=_get_str(row, "home_facility_name"),
        state_license_status=_get_str(row, "state_license_status"),
        state_license_days_left=lic_days,
        acls_status=_get_str(row, "acls_status"),
        acls_days_left=acls_days,
        active_privilege_count=priv_count,
        active_payer_count=payer_count,
        is_eligible=is_eligible,
        why_eligible=why_ok if is_eligible else [x for x in why_ok if "assumed" in x or "ACTIVE" in x],
        why_not=why_not if not is_eligible else [],
        time_to_ready_days=time_to_ready if not is_eligible else 0,
    )


def unique_ids(values: Iterable[Optional[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out

