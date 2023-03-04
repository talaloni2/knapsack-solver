import asyncio
import os

import aio_pika
import aioredis
from aioredis import Redis
from fastapi import Depends

from logic.algorithm_decider import AlgorithmDecider
from logic.algorithm_runner import AlgorithmRunner
from logic.items_claimer import ItemsClaimer
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solver.solver_loader import SolverLoader
from models.rabbit_connection_params import RabbitConnectionParams
from models.redis_connection_params import RedisConnectionParams


def get_rabbit_connection_params() -> RabbitConnectionParams:
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return RabbitConnectionParams(host=host, port=port, user=user, password=password)


def get_redis_connection_params() -> RedisConnectionParams:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return RedisConnectionParams(host=host, port=port)


def get_solver_queue() -> str:
    return os.getenv("SOLVER_QUEUE", "solver")


def get_algorithm_decider() -> AlgorithmDecider:
    return AlgorithmDecider()


def get_solver_loader():
    return SolverLoader()


def get_algorithm_runner(solver_loader=get_solver_loader()) -> AlgorithmRunner:
    return AlgorithmRunner(solver_loader)


def get_solver_router_producer(
    connection_params: RabbitConnectionParams = Depends(get_rabbit_connection_params),
    solver_queue: str = Depends(get_solver_queue),
) -> SolverRouterProducer:
    return SolverRouterProducer(connection_params, solver_queue)


def get_redis_api(connection_params: RedisConnectionParams = Depends(get_redis_connection_params)) -> Redis:
    return get_redis(connection_params)


def get_items_claimer_api(redis: Redis = Depends(get_redis_api)) -> ItemsClaimer:
    return get_items_claimer(redis)


def get_redis(connection_params: RedisConnectionParams = get_redis_connection_params()) -> Redis:
    host, port = connection_params
    return aioredis.from_url(f"redis://{host}:{port}")


def get_claimed_items_hash_name():
    return os.getenv("CLAIMED_ITEMS_HASH_NAME", "claimed_items")


def get_items_claimer(
    redis: Redis = get_redis(), claimed_items_hash_name: str = get_claimed_items_hash_name()
) -> ItemsClaimer:
    return ItemsClaimer(redis, claimed_items_hash_name)
