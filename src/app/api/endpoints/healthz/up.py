from fastapi import Response, status

from src.app.system.mdw_prometheus_metrics import global_registry


async def get_up() -> Response:
    """Сообщает о доступности сервиса."""
    up_status: int = status.HTTP_200_OK
    global_registry().write_up_status(up_status)
    return Response(status_code=up_status)
