from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from typing import Any, Optional

from databricks import sql
import requests

from settings import settings


class DatabricksNotConfigured(RuntimeError):
    pass


class DatabricksPermissionError(RuntimeError):
    pass


def _looks_like_permission_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "insufficient_permissions" in msg
        or "insufficient privileges" in msg
        or "sqlstate: 42501" in msg
        or "permission denied" in msg
    )


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]


_oauth_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def _get_access_token() -> str:
    """
    Prefer explicit PAT-style token (DATABRICKS_ACCESS_TOKEN / DATABRICKS_TOKEN).
    If absent, but OAuth M2M client credentials are present (Apps often provides these),
    fetch a short-lived access token and cache it.
    """
    if settings.databricks_access_token:
        return settings.databricks_access_token

    # OAuth M2M: fetch from workspace OIDC token endpoint
    if not (settings.databricks_client_id and settings.databricks_client_secret and settings.databricks_server_hostname):
        return ""

    now = time.time()
    cached = _oauth_token_cache.get("token")
    exp = float(_oauth_token_cache.get("expires_at") or 0.0)
    if cached and now < exp:
        return str(cached)

    token_url = f"https://{settings.databricks_server_hostname}/oidc/oauth2/v2.0/token"
    try:
        resp = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.databricks_client_id,
                "client_secret": settings.databricks_client_secret,
                "scope": "all-apis",
            },
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
        tok = body.get("access_token") or ""
        expires_in = int(body.get("expires_in") or 0)
        if not tok:
            return ""
        # refresh 60s early
        _oauth_token_cache["token"] = tok
        _oauth_token_cache["expires_at"] = now + max(0, expires_in - 60)
        return str(tok)
    except Exception:
        return ""


def _require_config() -> None:
    if not settings.databricks_server_hostname or not settings.databricks_http_path:
        raise DatabricksNotConfigured(
            "Databricks is not configured. Set DATABRICKS_SERVER_HOSTNAME and DATABRICKS_HTTP_PATH (or DATABRICKS_SQL_WAREHOUSE_HTTP_PATH)."
        )
    token = _get_access_token()
    if not token:
        raise DatabricksNotConfigured(
            "Databricks is not configured (no token). Set DATABRICKS_TOKEN/DATABRICKS_ACCESS_TOKEN, "
            "or provide DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET for OAuth M2M."
        )


@contextlib.contextmanager
def connect():
    _require_config()
    token = _get_access_token()
    with sql.connect(
        server_hostname=settings.databricks_server_hostname,
        http_path=settings.databricks_http_path,
        access_token=token,
    ) as conn:
        yield conn


def fetch_all(sql_text: str, params: Optional[dict[str, Any]] = None) -> QueryResult:
    """
    Execute a SELECT query and return rows as dicts.
    Uses DB-API style named parameters supported by databricks-sql-connector.
    """
    params = params or {}
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text, params)
                cols = [d[0] for d in cur.description] if cur.description else []
                data = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        if _looks_like_permission_error(e):
            raise DatabricksPermissionError(str(e)) from e
        raise
    rows = [dict(zip(cols, r)) for r in data]
    return QueryResult(columns=cols, rows=rows)


def fetch_scalar(sql_text: str, params: Optional[dict[str, Any]] = None) -> Any:
    res = fetch_all(sql_text, params)
    if not res.rows:
        return None
    first_row = res.rows[0]
    return next(iter(first_row.values())) if first_row else None


def execute(sql_text: str, params: Optional[dict[str, Any]] = None) -> None:
    """
    Execute a non-SELECT statement (INSERT/UPDATE/DELETE).
    """
    params = params or {}
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text, params)
    except Exception as e:  # noqa: BLE001
        if _looks_like_permission_error(e):
            raise DatabricksPermissionError(str(e)) from e
        raise


def fetch_paged(
    data_sql: str,
    count_sql: str,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    items = fetch_all(data_sql, params).rows
    total = int(fetch_scalar(count_sql, params) or 0)
    return items, total


def is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        s in msg
        for s in [
            "temporarily unavailable",
            "timeout",
            "timed out",
            "connection",
            "throttl",
            "rate limit",
            "too many requests",
        ]
    )


def with_retry(fn, *, attempts: int = 3, base_delay_s: float = 0.4):
    last: Optional[Exception] = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if i == attempts - 1 or not is_transient_error(e):
                raise
            time.sleep(base_delay_s * (2**i))
    raise last  # pragma: no cover

