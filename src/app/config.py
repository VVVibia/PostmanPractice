from pathlib import Path
from typing import Type, TypeVar

import yaml
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigModel(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CC_', env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return env_settings, init_settings, file_secret_settings


class ServiceConfig(BaseModel):
    name: str
    version: str
    port: int


class PostgresConfig(BaseModel):
    user: str
    password: SecretStr
    host: str
    port: int
    db_name: str

    @property
    def dsn(self):
        return 'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}'.format(
            user=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            db_name=self.db_name,
        )


class JwtConfig(BaseModel):
    secret: SecretStr
    access_token_expire_minutes: int


class CreditCardConfig(BaseModel):
    exp_date_in_years: int
    default_limit: int


class PhotoServiceConfig(BaseModel):
    url: str
    timeout: float


class Config(ConfigModel):
    """Общий набор полей для конфигурации приложения."""

    service: ServiceConfig
    logging: dict
    postgres: PostgresConfig
    jwt: JwtConfig
    credit_card: CreditCardConfig
    photo_service: PhotoServiceConfig


TC = TypeVar('TC', bound=ConfigModel)


def read_config(config_path: str, model: Type[TC]) -> TC:
    """Метод для создания pydantic объекта из yaml-конфига."""
    config_raw = yaml.safe_load(Path(config_path).read_text())
    return model(**config_raw)
