from __future__ import annotations

from typing import NamedTuple


class RabbitConnectionParams(NamedTuple):
    host: str
    port: int
    user: str
    password: str
