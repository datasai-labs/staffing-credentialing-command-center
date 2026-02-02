from fastapi import APIRouter

from models.common import DatabricksHealthResponse
from services import databricks
from services.databricks import DatabricksNotConfigured
from settings import settings

from models.common import HealthcheckResponse

router = APIRouter()


@router.get("/healthcheck", response_model=HealthcheckResponse)
def healthcheck() -> HealthcheckResponse:
    return HealthcheckResponse()


@router.get("/healthcheck/databricks", response_model=DatabricksHealthResponse)
def databricks_healthcheck() -> DatabricksHealthResponse:
    configured = bool(
        settings.databricks_server_hostname
        and settings.databricks_http_path
        and (settings.databricks_access_token or (settings.databricks_client_id and settings.databricks_client_secret))
    )
    try:
        _ = databricks.fetch_scalar("SELECT 1")
        return DatabricksHealthResponse(
            configured=configured,
            can_connect=True,
            message="ok",
            server_hostname_set=bool(settings.databricks_server_hostname),
            http_path_set=bool(settings.databricks_http_path),
            access_token_set=bool(settings.databricks_access_token or settings.databricks_client_id),
            catalog=settings.databricks_catalog,
            schema_gold=settings.databricks_schema_gold,
            use_mock_data=settings.use_mock_data,
        )
    except DatabricksNotConfigured as e:
        return DatabricksHealthResponse(
            configured=False,
            can_connect=False,
            message=str(e),
            server_hostname_set=bool(settings.databricks_server_hostname),
            http_path_set=bool(settings.databricks_http_path),
            access_token_set=bool(settings.databricks_access_token or (settings.databricks_client_id and settings.databricks_client_secret)),
            catalog=settings.databricks_catalog,
            schema_gold=settings.databricks_schema_gold,
            use_mock_data=settings.use_mock_data,
        )
    except Exception as e:  # noqa: BLE001
        return DatabricksHealthResponse(
            configured=configured,
            can_connect=False,
            message=str(e)[:500],
            server_hostname_set=bool(settings.databricks_server_hostname),
            http_path_set=bool(settings.databricks_http_path),
            access_token_set=bool(settings.databricks_access_token or (settings.databricks_client_id and settings.databricks_client_secret)),
            catalog=settings.databricks_catalog,
            schema_gold=settings.databricks_schema_gold,
            use_mock_data=settings.use_mock_data,
        )

