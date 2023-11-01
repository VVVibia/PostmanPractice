import asyncio
import datetime

import pytest
from dateutil.relativedelta import relativedelta
from faker import Faker
from httpx import AsyncClient
from sqlalchemy import delete

from src.app.api.schemas.common import Sex
from src.app.config import Config, read_config
from src.app.external.db.models import CreditCardModel, UserModel
from src.app.service import prepare_app
from src.app.system import environment
from src.app.system.mdw_prometheus_metrics import global_registry
from tests.utils import clear_metrics

fake = Faker(locale='ru-RU')


@pytest.fixture(scope='session')
def config():
    """Базовая конфигурация сервиса в виде pydantic объекта."""
    config = read_config('src/config/config.yml', Config)
    return config


@pytest.fixture(scope='session')
def event_loop():
    """Event loop с измененным scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def app(config):
    """Возвращает объект приложения FastAPI"""
    environment.initialize(config)
    _app = prepare_app(config)
    return _app


@pytest.fixture(scope='session')
async def cli(app):
    """Возвращает асинхронный клиент приложения"""
    async with AsyncClient(app=app, base_url='http://testserver') as client:
        yield client


@pytest.fixture(scope='session')
def db(app):
    """Фикстура возвращает объект контейнера базы данных приложения"""
    return app.state.container.db()


@pytest.fixture
async def session(db):
    """Фикстура возвращает сессию подключения к БД"""
    async with db.session() as session:
        yield session


@pytest.fixture(scope='session')
def security(app):
    """Фикстура возвращает объект контейнера сервиса безопасности приложения"""
    return app.state.container.security()


@pytest.fixture(scope='session', autouse=True)
async def prepare_db(db):
    """
    Фикстура заполняет БД данными клиентов. Выполняется один раз за прогон.
    После выполнения тестов добавленыые данные удаляются.
    """
    users = [UserModel(
            email=fake.email(),
            hashed_password=fake.password(),
            full_name=fake.name(),
            income=fake.random_int(10_000_00, 50_000_00),
            another_loans=fake.boolean(),
            birth_date=fake.date_of_birth(),
            sex=fake.random_element([Sex.male, Sex.female]),
        ) for _ in range(10)]

    async with db.session() as session:
        async with session.begin():
            session.add_all(users)
        # for user in users:
        #     await session.refresh(user)

    credit_cards = [CreditCardModel(
        user_id=user.id,
        limit=10_000_00,
        balance=5_000_00,
        exp_date=fake.date_this_year()
    ) for user in users]

    async with db.session() as session:
        async with session.begin():
            session.add_all(credit_cards)

    yield

    async with db.session() as session:
        async with session.begin():
            for credit_card in credit_cards:
                await session.delete(credit_card)
            for user in users:
                await session.delete(user)


@pytest.fixture(scope='session')
def test_user_email():
    return fake.email()


@pytest.fixture(scope='session')
def test_user_password():
    return fake.password()


@pytest.fixture
async def add_test_user(request, security, session, test_user_email, test_user_password):
    """
    Фикстура добавляет тестового клиента.
    Если необходимо указать определенные параметры клиента, их необходимо передать через словарь с нужными значениями.
    Данные передаются в параметр request через @pytest.mark.fixture_name_data(param_name) перед тестом.

    Поля email и password задаются автоматически.
    По умолчанию будет создан пользователь, который только что зарегистрировался, без дополнительных данных.
    """
    if user_data := request.node.get_closest_marker('add_test_user_data'):
        user_data, = user_data.args

    password = security.get_password_hash(test_user_password)
    if not user_data:
        user = UserModel(email=test_user_email, hashed_password=password)
    else:
        user_data['email'] = test_user_email
        user_data['hashed_password'] = password
        user = UserModel(**user_data)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    # Освобождаем ссылки на экземпляр в текущей сессии
    session.expunge_all()

    yield user

    await session.execute(delete(UserModel).where(UserModel.id == user.id))
    await session.commit()


@pytest.fixture
async def add_test_credit_card(security, session, add_test_user):
    credit_card = CreditCardModel(
        user_id=add_test_user.id,
        limit=30_000_00,
        balance=10_000_00,
        active=True,
        exp_date=datetime.date.today() + relativedelta(years=1)
    )
    session.add(credit_card)
    await session.commit()
    await session.refresh(credit_card)
    # Освобождаем ссылки на экземпляр в текущей сессии
    session.expunge(credit_card)

    yield credit_card

    await session.execute(delete(CreditCardModel).where(CreditCardModel.id == credit_card.id))
    await session.commit()


@pytest.fixture
async def delete_registered_user(test_user_email, session):
    yield
    await session.execute(delete(UserModel).where(UserModel.email == test_user_email))
    await session.commit()


@pytest.fixture
async def auth_header(cli, test_user_password, test_user_email, add_test_user):
    resp = await cli.post('/auth/access_token', data={'username': test_user_email, 'password': test_user_password})
    token = resp.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def activity_registry():
    activity_reg = global_registry()._activity_reg
    clear_metrics(activity_reg)
    return activity_reg



