from fastapi import APIRouter, FastAPI

from src.app.api.endpoints import auth, credit_card, user
from src.app.api.endpoints.healthz import metrics, ready, up
from src.app.system.mdw_fastapi.api.docs import add_delete, add_get, add_patch, add_post
from src.app.system.mdw_fastapi.api.route import LoggedRoute


def setup_routes(app: FastAPI):
    """Инициализирует маршруты приложения."""
    monitoring_router = APIRouter(prefix='/healthz', tags=['healthz'])
    add_get(monitoring_router, '/up', up.get_up)
    add_get(monitoring_router, '/ready', ready.get_ready)
    add_get(monitoring_router, '/metrics', metrics.get_metrics)
    add_delete(monitoring_router, '/metrics', metrics.delete_metrics)
    app.include_router(monitoring_router)

    auth_router = APIRouter(prefix='/auth', tags=['auth'])
    add_post(auth_router, '/access_token', auth.access_token)
    app.include_router(auth_router)

    user_router = APIRouter(prefix='/user', tags=['user'], route_class=LoggedRoute)
    add_post(user_router, '/register', user.register)
    add_get(user_router, '', user.get_user_me)
    add_patch(user_router, '', user.update_user)
    add_post(user_router, '/document', user.document_photo)
    add_post(user_router, '/face', user.face_photo)
    app.include_router(user_router)

    credit_card_router = APIRouter(
        prefix='/credit_card',
        tags=['credit_card'],
        route_class=LoggedRoute,
    )
    add_post(credit_card_router, '/new', credit_card.add_card)
    add_post(credit_card_router, '/increase_limit', credit_card.increase_limit)
    add_get(credit_card_router, '', credit_card.get_current_card)
    add_post(credit_card_router, '/close', credit_card.close_card)
    app.include_router(credit_card_router)
