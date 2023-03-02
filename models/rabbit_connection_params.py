from __future__ import annotations

import os
from typing import NamedTuple


def get_rabbit_connection_params() -> RabbitConnectionParams:
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return RabbitConnectionParams(host=host, port=port, user=user, password=password)


class RabbitConnectionParams(NamedTuple):
    host: str
    port: int
    user: str
    password: str
