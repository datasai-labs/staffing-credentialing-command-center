from __future__ import annotations

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Databricks SQL connector settings
    databricks_server_hostname: Optional[str] = Field(default=None, alias="DATABRICKS_SERVER_HOSTNAME")
    databricks_http_path: Optional[str] = Field(default=None, alias="DATABRICKS_HTTP_PATH")
    databricks_access_token: Optional[str] = Field(default=None, alias="DATABRICKS_ACCESS_TOKEN")
    # Optional OAuth M2M auth (Databricks Apps often injects these)
    databricks_client_id: Optional[str] = Field(default=None, alias="DATABRICKS_CLIENT_ID")
    databricks_client_secret: Optional[str] = Field(default=None, alias="DATABRICKS_CLIENT_SECRET")

    databricks_catalog: str = Field(default="rtpa_catalog", alias="DATABRICKS_CATALOG")
    databricks_schema_gold: str = Field(default="credentialing_gold", alias="DATABRICKS_SCHEMA_GOLD")
    databricks_schema_silver: str = Field(default="credentialing_silver", alias="DATABRICKS_SCHEMA_SILVER")
    databricks_schema_ref: str = Field(default="credentialing_ref", alias="DATABRICKS_SCHEMA_REF")

    cors_allow_origins: Optional[str] = Field(default=None, alias="CORS_ALLOW_ORIGINS")

    kpi_cache_ttl_seconds: int = Field(default=60, alias="KPI_CACHE_TTL_SECONDS")
    # In prod we should not silently serve mock data. If unset, defaults to True for dev, False otherwise.
    allow_mock_data: Optional[bool] = Field(default=None, alias="ALLOW_MOCK_DATA")

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local"}

    @property
    def use_mock_data(self) -> bool:
        if self.allow_mock_data is None:
            return self.is_dev
        return bool(self.allow_mock_data)

    def normalize_databricks(self) -> None:
        """
        Databricks Apps commonly provides ambient auth via DATABRICKS_HOST + DATABRICKS_TOKEN.
        Also, Apps can inject the SQL Warehouse HTTP path via DATABRICKS_SQL_WAREHOUSE_HTTP_PATH.
        We map those to the databricks-sql-connector variables if the explicit ones aren't set.
        """
        if not self.databricks_server_hostname:
            host = os.getenv("DATABRICKS_HOST") or ""
            host = host.replace("https://", "").replace("http://", "").strip().strip("/")
            if host:
                object.__setattr__(self, "databricks_server_hostname", host)  # type: ignore[misc]
        if not self.databricks_http_path:
            # Apps may provide either:
            # - full http path: /sql/1.0/warehouses/<id>
            # - just the warehouse id: <id>
            raw = (os.getenv("DATABRICKS_SQL_WAREHOUSE_HTTP_PATH") or os.getenv("WAREHOUSE_ID") or "").strip()
            if raw:
                if "/" in raw:
                    object.__setattr__(self, "databricks_http_path", raw)  # type: ignore[misc]
                else:
                    object.__setattr__(self, "databricks_http_path", f"/sql/1.0/warehouses/{raw}")  # type: ignore[misc]
        if not self.databricks_access_token:
            tok = os.getenv("DATABRICKS_TOKEN") or ""
            if tok:
                object.__setattr__(self, "databricks_access_token", tok)  # type: ignore[misc]

    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins:
            return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]
        if self.is_dev:
            return ["http://localhost:5173"]
        return []


settings = Settings()
settings.normalize_databricks()

