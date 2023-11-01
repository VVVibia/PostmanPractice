from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Response, status

from src.app.system.mdw_fastapi.api.docs import openapi
from src.app.system.mdw_prometheus_metrics import global_registry
from src.app.system.mdw_prometheus_metrics.service.external import ExternalComponentsChecker
from src.app.system.resources import ApplicationContainer


@inject
@openapi(
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {'description': 'Сервис не готов принимать запросы.'},
    },
)
async def get_ready(
    components: ExternalComponentsChecker =
    Depends(Provide[ApplicationContainer.components_checker]),
) -> Response:
    """Сообщает о готовности сервиса к обработке запросов."""
    ready_status = await components.major_components_status()
    http_status = status.HTTP_200_OK if ready_status else status.HTTP_503_SERVICE_UNAVAILABLE
    global_registry().write_ready_status(http_status)
    return Response(status_code=http_status)
