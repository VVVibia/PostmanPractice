from asyncio import TimeoutError
from unittest.mock import AsyncMock

import pytest

from app.external.http_errors import HttpClientTimeoutError
from app.services.photo import PhotoService, PhotoServiceConfig


@pytest.fixture
def image_mock():
    """Мок файла для отправки в PhotoService."""
    image = AsyncMock()
    image.read.return_value = b'photo_content'
    image.content_type = 'image/jpeg'
    image.filename = 'photo.jpg'

    return image


@pytest.fixture
def photo_service_config(config):
    """Базовая конфигурация объекта PhotoService."""
    return PhotoServiceConfig(
        url=config.photo_service.url,
        timeout=config.photo_service.timeout
    )


async def test_photo_service_timeout_error(photo_service_config, image_mock, caplog):
    """Проверка поведения при TimeoutError запросов к сервису валидации фотографий."""

    photo_service_session = AsyncMock()
    photo_service_session.post.side_effect = TimeoutError

    photo_service = PhotoService(photo_service_session, photo_service_config)

    with pytest.raises(HttpClientTimeoutError):
        await photo_service.validate_photo(image_mock, 'doc')

    assert f'PhotoService unavailable by {photo_service._request_timeout} secs timeout.' in caplog.messages
