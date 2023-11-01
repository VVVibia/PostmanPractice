import datetime
import json
import logging
import os
import traceback
from typing import Any, Dict

import msgpack
from pytz import timezone
from pytz.reference import LocalTimezone

from . import context

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
_TIMEZONE = os.environ.get('TZ', None)
_TZINFO = timezone(_TIMEZONE) if _TIMEZONE else LocalTimezone()
_MESSAGE_PARAM = 'message'
_CONTENT_PARAM = 'content'

_Json = Dict[str, Any]


def to_str_recursive(data):
    try:
        msgpack.packb(data)
    except msgpack.PackException:
        if isinstance(data, dict):
            return {key: to_str_recursive(data[key]) for key in data}
        elif isinstance(data, list):
            return [to_str_recursive(elem) for elem in data]
        return str(data)
    return data


def format_by_dp_standard(record):
    """Форматирует логируемую информацию по стандарту ДП.
    """
    formatted_record = {
        'timestamp': datetime.datetime.now(tz=_TZINFO).strftime(_TIMESTAMP_FORMAT),
        **context.additional_context.get(),
        'version': context.version,
        'message': {
            'logger': record.name,
            'severity': record.levelname,
            'class': f'{record.module}.{record.funcName}',
            'content': {
                'data': to_str_recursive(record.msg),
            } if isinstance(record.msg, dict) else {
                'text': record.getMessage(),
            }
        },
        'name': context.service,
        'component': 'backend',
    }

    if record.exc_info:
        formatted_record['message']['content'].update(**{
            'stack_trace': ''.join(traceback.format_exception(*record.exc_info)),
            'exc_type': str(record.exc_info[0]),
        })
    return formatted_record


class Formatter(logging.Formatter):
    """Форматтер для консольных логов."""

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        formatted_record = format_by_dp_standard(record)
        return json.dumps(
            formatted_record,
            skipkeys=True,
            default=str,
            ensure_ascii=False,
        )
