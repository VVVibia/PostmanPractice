import logging
from asyncio import TimeoutError
from http import HTTPStatus

from aiohttp import ClientResponseError, ClientSession, FormData
from fastapi import UploadFile
from yarl import URL

from src.app.config import PhotoServiceConfig
from src.app.external.http_errors import HttpClientError, HttpClientTimeoutError


class PhotoService:
    """Клиент для получения лиц по списку фото."""

    def __init__(
        self,
        session: ClientSession,
        config: PhotoServiceConfig,
    ):
        self._session = session
        self._url = URL(config.url)
        self._request_timeout = config.timeout

    async def validate_photo(self, photo: UploadFile, photo_type: str):
        form_data = FormData()
        form_data.add_field(
            'photo',
            await photo.read(),
            content_type=photo.content_type,
            filename=photo.filename,
        )
        endpoint = 'face'
        if photo_type == 'doc':
            endpoint = 'doc'
        try:
            response = await self._session.post(
                self._url / endpoint,
                data=form_data,
                timeout=self._request_timeout,
            )
        except TimeoutError:
            logging.exception(
                f'PhotoService unavailable by {self._request_timeout} secs timeout.',
            )
            raise HttpClientTimeoutError(
                service_name='PhotoService',
                timeout=self._request_timeout,
            )
        except ClientResponseError as exc:
            logging.exception(
                f'PhotoService error: {exc}',
            )
            raise HttpClientError(detail='PhotoService error')
        if response.status != HTTPStatus.OK:
            resp_text = await response.text()
            raise HttpClientError(
                detail=f'Response status code {response.status}: {resp_text}',
            )
        raw_data = await response.json()
        logging.info({'PhotoService response': raw_data})
        return raw_data['status'] == 'OK'

    async def is_connected(self):
        response = await self._session.get(
            self._url / 'healthz' / 'up',
            timeout=self._request_timeout,
        )
        return response.status == HTTPStatus.OK
