import os

import aioredis
from aioredis import Redis
from fastapi import Depends

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
from models.config.configuration import Config
from models.knapsack_router_dto import RouterSolveRequest
from models.config.rabbit_connection_params import RabbitConnectionParams
from models.config.redis_connection_params import RedisConnectionParams


def get_config() -> Config:
    return Config(
        rabbit_connection_params=RabbitConnectionParams(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            user=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        ),
        redis_connection_params=RedisConnectionParams(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
        ),
        solver_queue=os.getenv("SOLVER_QUEUE", "solver"),
        items_claim_hash=os.getenv("RUNNING_SOLVERS_CLAIM_HASH", "running_solvers_claims"),
        suggested_solutions_claims_hash=os.getenv("SUGGESTED_SOLUTIONS_CLAIM_HASH", "suggested_solutions_claims"),
        running_knapsack_claims_hash=os.getenv("RUNNING_KNAPSACK_CLAIM_HASH", "running_knapsack_claims"),
        solutions_channel_prefix=os.getenv("SOLUTIONS_CHANNEL_PREFIX", "solutions"),
        wait_for_report_timeout_seconds=float(os.getenv("WAIT_FOR_REPORT_TIMEOUT_SECONDS", "60")),
        suggested_solutions_hash=os.getenv("SOLUTION_SUGGESTIONS_HASH_NAME", "solution_suggestions"),
        accepted_solutions_list=os.getenv("ACCEPTED_SOLUTION_HASH_NAME", "solution_suggestions"),
        clean_old_suggestion_interval_seconds=int(os.getenv("CLEAN_OLD_SUGGESTION_INTERVAL_SECONDS", "30")),
        clean_old_accepted_solutions_interval_seconds=int(os.getenv("CLEAN_OLD_ACCEPTED_SOLUTIONS_INTERVAL_SECONDS", f"{60 * 30}")),
        suggestion_ttl_seconds=int(os.getenv("SUGGESTION_TTL_SECONDS", "60")),
        accepted_solution_ttl_seconds=int(os.getenv("ACCEPTED_SOLUTION_TTL_SECONDS", f"{60 * 60 * 4}")),
        accepted_solutions_prefect_count=int(os.getenv("ACCEPTED_SOLUTIONS_PREFECT_COUNT", "5")),
    )


def get_algorithm_decider() -> AlgorithmDecider:
    return AlgorithmDecider()


def get_solver_loader():
    return SolverLoader()


def get_algorithm_runner(solver_loader=get_solver_loader()) -> AlgorithmRunner:
    return AlgorithmRunner(solver_loader)


def get_solver_router_producer(config: Config = Depends(get_config)) -> SolverRouterProducer:
    return SolverRouterProducer(config.rabbit_connection_params, config.solver_queue)


def get_redis_api(config: Config = Depends(get_config)) -> Redis:
    return get_redis(config)


def get_claims_service_api(redis: Redis = Depends(get_redis_api)) -> ClaimsService:
    return get_claims_service(redis)


def get_redis(config: Config = get_config()) -> Redis:
    host, port = config.redis_connection_params
    return aioredis.from_url(f"redis://{host}:{port}")


def get_claims_service(redis: Redis = get_redis(), config: Config = get_config()) -> ClaimsService:
    return ClaimsService(
        redis, config.items_claim_hash, config.suggested_solutions_claims_hash, config.running_knapsack_claims_hash
    )


def get_rabbit_channel_context(config: Config = get_config()) -> RabbitChannelContext:
    return RabbitChannelContext(config.rabbit_connection_params)


def get_time_service() -> TimeService:
    return TimeService()


def get_suggested_solutions_service(
    redis: Redis = get_redis(),
    claims_service: ClaimsService = get_claims_service(),
    time_service: TimeService = get_time_service(),
    config: Config = get_config(),
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis, claims_service, time_service, config.suggested_solutions_hash, config.accepted_solutions_list
    )


def get_suggested_solutions_service_api(
    redis: Redis = Depends(get_redis_api),
    claims_service: ClaimsService = Depends(get_claims_service_api),
    time_service: TimeService = Depends(get_time_service),
    config: Config = Depends(get_config),
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis, claims_service, time_service, config.suggested_solutions_hash, config.accepted_solutions_list
    )


def get_solution_reporter(
    redis: Redis = get_redis(),
    config: Config = get_config(),
    suggested_solutions_service: SuggestedSolutionsService = get_suggested_solutions_service(),
) -> SolutionReporter:
    return SolutionReporter(redis, config.solutions_channel_prefix, suggested_solutions_service)


def get_solution_report_waiter_api_route_solve(
    request: RouterSolveRequest, redis: Redis = Depends(get_redis_api), config: Config = Depends(get_config),
) -> SolutionReportWaiter:
    return SolutionReportWaiter(redis, config.solutions_channel_prefix, request.knapsack_id, config.wait_for_report_timeout_seconds)
