from __future__ import annotations

from typing import NamedTuple


class RedisConnectionParams(NamedTuple):
    host: str
    port: int
