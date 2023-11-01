# Разработка сервиса

## Рабочее окружение
Для начала разработки необходимо настроить рабочее окружение. Нам понадобятся следующие системные зависимости: 
- [python](https://www.python.org/downloads/) версии 3.10 или выше
- менеджер зависимостей [poetry](https://python-poetry.org/docs/#installation) версии 1.1 или выше
- инструмент для коммит-хуков [pre-commit](https://pre-commit.com/)
- [Docker](https://www.docker.com/)

Настройка окружения:
### Склонировать репозиторий

### Установить зависимости. Зависимости установятся в виртуальное окружение.
 ```shell script
 poetry install -E lint -E migrations -E tests
 ```

### Настроить commit хуки.
 ```shell script
 pre-commit install --install-hooks
 ```

### Настроить БД PostgreSQL
```shell script
docker run -d -e POSTGRES_PASSWORD=password -e POSTGRES_USER=admin -e POSTGRES_DB=credit_card -p 5432:5432 --name=shift_postgres postgres:12.9
cd src
alembic upgrade head
```
### Иметь рабочий PhotoService
Для этого склонировать соответствующий репозиторий и запустить сервис. 




## Дополнительные команды при разработке

### Создание миграций
```shell script
alembic revision --autogenerate -m "MESSAGE"
```

###  Запуск линтера
```shell script
git add . && pre-commit run lint --all-files
```

###  Запуск isort
```shell script
git add . && pre-commit run isort --all-files
```