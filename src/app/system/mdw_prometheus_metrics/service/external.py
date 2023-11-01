import asyncio
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Awaitable, Callable, Iterable, List

from .collector import ServiceCollector, Severity


@dataclass
class Component:
    """Атрибуты внешнего компонента по стандарту ДП."""

    name: str
    type: str
    severity: Severity
    checker: Callable[[], Awaitable[bool]]


class ExternalComponentsChecker:
    """Проверяет доступность внешних компонентов."""

    def __init__(
        self,
        components: Iterable[Component] = (),
        callbacks: Iterable[Callable[[Component, asyncio.Task], None]] = (),
    ):
        """Зависимости."""
        self._callbacks = callbacks
        self._minor_components: List[Component] = []
        self._major_components: List[Component] = []
        self.add_components(components)

    def add_component(self, external_component: Component):
        """Добавить компонент."""
        if external_component.severity == Severity.MINOR:
            components_container = self._minor_components
        elif external_component.severity == Severity.MAJOR:
            components_container = self._major_components
        else:
            raise ValueError('Unsupported component severity.')
        components_container.append(external_component)

    def add_components(self, external_components: Iterable[Component]):
        """Добавить список компонентов."""
        for component in external_components:
            self.add_component(component)

    async def major_components_status(self) -> bool:
        """Проверка MAJOR компонентов сервиса и запись метрик доступности.

        :return: готовность всех внешних компонентов.
        """
        return await self._check_component_statuses(self._major_components)

    async def minor_components_status(self) -> bool:
        """Проверка MINOR компонентов сервиса и запись метрик доступности.

        :return: готовность всех внешних компонентов.
        """
        return await self._check_component_statuses(self._minor_components)

    async def _check_component_statuses(self, components) -> bool:
        tasks = {
            asyncio.get_event_loop().create_task(component.checker()): component
            for component in components
        }
        component_statuses = await asyncio.gather(
            *tasks.keys(),
            return_exceptions=True,
        )
        for task_res, component in tasks.items():
            for callback in self._callbacks:
                callback(component, task_res)
        return all(res is True for res in component_statuses)


def collect_component_metrics(
    collector: ServiceCollector,
    component: Component,
    finished_check: asyncio.Task,
):
    res = finished_check.exception() or finished_check.result()
    collector.write_ready_component_status(
        HTTPStatus.OK.value if res is True else HTTPStatus.SERVICE_UNAVAILABLE.value,
        component=component.name,
        component_type=component.type,
        severity=component.severity,
    )


def log_check_exception(
    component: Component,
    finished_check: asyncio.Task,
):
    res = finished_check.exception() or finished_check.result()
    if isinstance(res, Exception) or res is False:
        logging.exception(
            '{severity} external {ctype} "{component}" unavailable'.format(
                severity=component.severity.name,
                ctype=component.type,
                component=component.name,
            ),
            exc_info=res,
        )
