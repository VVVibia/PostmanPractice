import json
import logging
import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

logger = logging.getLogger('app.api')


class LoggedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.monotonic()
            start_log = {'selector': 'request_data'}
            try:
                req_body = await request.json()
            except Exception:  # noqa
                pass
            else:
                start_log['body'] = jsonable_encoder(req_body)

            if request.query_params:
                start_log['query_params'] = dict(request.query_params)

            fd = await request.form()
            if fd:
                start_log['form_data'] = {name: value.filename for name, value in fd.items()}
            logger.info(start_log)

            status_code = status.HTTP_200_OK
            resp_body = None
            try:
                response: Response = await original_route_handler(request)
                status_code = response.status_code
                if response.body:
                    resp_body = json.loads(response.body.decode())
            except HTTPException as exc:
                status_code = exc.status_code
                resp_body = {'detail': exc.detail}
                raise
            except RequestValidationError as exc:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                resp_body = {'detail': jsonable_encoder(exc.errors())}
                raise
            except Exception as exc:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                resp_body = jsonable_encoder({
                    'detail': [
                        {
                            'loc': [],
                            'msg': str(exc),
                            'type': str(type(exc)),
                        },
                    ],
                })
                raise
            finally:
                logger.info({
                    'selector': 'response_data',
                    'status_code': status_code,
                    'response': resp_body,
                    'time': time.monotonic() - start_time,
                })

            return response

        return custom_route_handler
