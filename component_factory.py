import os

import aioredis
from aioredis import Redis
from fastapi import Depends
from fastapi.requests import Request

from logic.algorithm_decider import AlgorithmDecider
from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_report_waiter import SolutionReportWaiter
from logic.solution_reporter import SolutionReporter
from logic.solver.solver_loader import SolverLoader
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.knapsack_router_dto import RouterSolveRequest
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


def get_claims_service_api(redis: Redis = Depends(get_redis_api)) -> ClaimsService:
    return get_claims_service(redis)


def get_redis(connection_params: RedisConnectionParams = get_redis_connection_params()) -> Redis:
    host, port = connection_params
    return aioredis.from_url(f"redis://{host}:{port}")


def items_claim_hash():
    return os.getenv("RUNNING_SOLVERS_CLAIM_HASH", "running_solvers_claims")


def suggested_solutions_claims_hash():
    return os.getenv("SUGGESTED_SOLUTIONS_CLAIM_HASH", "suggested_solutions_claims")


def running_knapsack_claims_hash():
    return os.getenv("RUNNING_KNAPSACK_CLAIM_HASH", "running_knapsack_claims")


def get_claims_service(
    redis: Redis = get_redis(),
    items_claim_hash_name: str = items_claim_hash(),
    suggested_solutions_claims_hash_name: str = suggested_solutions_claims_hash(),
    running_knapsack_claims_hash_name: str = running_knapsack_claims_hash(),
) -> ClaimsService:
    return ClaimsService(
        redis, items_claim_hash_name, suggested_solutions_claims_hash_name, running_knapsack_claims_hash_name
    )


def get_rabbit_channel_context(
    connection_params: RabbitConnectionParams = get_rabbit_connection_params(),
) -> RabbitChannelContext:
    return RabbitChannelContext(connection_params)


def get_solutions_channel_prefix() -> str:
    return os.getenv("SOLUTIONS_CHANNEL_PREFIX", "solutions")


def get_suggested_solutions_hash_name() -> str:
    return os.getenv("SOLUTION_SUGGESTIONS_HASH_NAME", "solution_suggestions")


def get_accepted_solutions_list_name() -> str:
    return os.getenv("ACCEPTED_SOLUTION_HASH_NAME", "solution_suggestions")


def get_time_service() -> TimeService:
    return TimeService()


def get_suggested_solutions_service(
    redis: Redis = get_redis(),
    claims_service: ClaimsService = get_claims_service(),
    time_service: TimeService = get_time_service(),
    solution_suggestions_hash_name: str = get_suggested_solutions_hash_name(),
    accepted_solutions_list_name: str = get_accepted_solutions_list_name(),
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis, claims_service, time_service, solution_suggestions_hash_name, accepted_solutions_list_name
    )


def get_suggested_solutions_service_api(
    redis: Redis = Depends(get_redis_api),
    claims_service: ClaimsService = Depends(get_claims_service_api),
    time_service: TimeService = Depends(get_time_service),
    solution_suggestions_hash_name: str = Depends(get_suggested_solutions_hash_name),
    accepted_solutions_list_name: str = Depends(get_accepted_solutions_list_name),
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis, claims_service, time_service, solution_suggestions_hash_name, accepted_solutions_list_name
    )


def get_solution_reporter(
    redis: Redis = get_redis(),
    solutions_channel_prefix: str = get_solutions_channel_prefix(),
    suggested_solutions_service: SuggestedSolutionsService = get_suggested_solutions_service(),
) -> SolutionReporter:
    return SolutionReporter(redis, solutions_channel_prefix, suggested_solutions_service)


def get_wait_for_report_timeout_seconds() -> float:
    return float(os.getenv("WAIT_FOR_REPORT_TIMEOUT_SECONDS", "60"))


def get_solution_report_waiter_api_route_solve(
    request: RouterSolveRequest,
    redis: Redis = Depends(get_redis_api),
    solutions_channel_prefix: str = Depends(get_solutions_channel_prefix),
    wait_for_report_timeout_seconds: int = Depends(get_wait_for_report_timeout_seconds),
):
    return SolutionReportWaiter(redis, solutions_channel_prefix, request.knapsack_id, wait_for_report_timeout_seconds)
