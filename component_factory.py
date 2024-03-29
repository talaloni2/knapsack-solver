import os

import aio_pika.abc
import aioredis
from aioredis import Redis
from fastapi import Depends
from httpx import AsyncClient

from logic.algorithm_decider import AlgorithmDecider
from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.cluster_availability_service import ClusterAvailabilityService
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_maintainer import SolutionMaintainer
from logic.solution_report_waiter import SolutionReportWaiter
from logic.solution_reporter import SolutionReporter
from logic.solver.solver_loader import SolverLoader
from logic.subscriptions_service import SubscriptionsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.config.configuration import Config, DeploymentType
from models.knapsack_router_dto import RouterSolveRequest
from models.config.rabbit_connection_params import RabbitConnectionParams
from models.config.redis_connection_params import RedisConnectionParams


def get_config() -> Config:
    raw_deployment_type = os.getenv("DEPLOYMENT_TYPE")
    return Config(
        server_port=int(os.getenv("SERVER_PORT", "8000")),
        deployment_type=raw_deployment_type and DeploymentType(raw_deployment_type),
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
        accepted_solutions_list=os.getenv("ACCEPTED_SOLUTION_HASH_NAME", "accepted_solutions"),
        clean_old_suggestion_interval_seconds=int(os.getenv("CLEAN_OLD_SUGGESTION_INTERVAL_SECONDS", "30")),
        clean_old_accepted_solutions_interval_seconds=int(
            os.getenv("CLEAN_OLD_ACCEPTED_SOLUTIONS_INTERVAL_SECONDS", f"{60 * 30}")
        ),
        suggestion_ttl_seconds=int(os.getenv("SUGGESTION_TTL_SECONDS", "60")),
        accepted_solution_ttl_seconds=int(os.getenv("ACCEPTED_SOLUTION_TTL_SECONDS", f"{60 * 60 * 4}")),
        accepted_solutions_prefect_count=int(os.getenv("ACCEPTED_SOLUTIONS_PREFECT_COUNT", "5")),
        solvers_moderate_busy_threshold=int(os.getenv("SOLVERS_MODERATE_BUSY_THRESHOLD", "40")),
        solvers_busy_threshold=int(os.getenv("SOLVERS_BUSY_THRESHOLD", "60")),
        solvers_very_busy_threshold=int(os.getenv("SOLVERS_VERY_BUSY_THRESHOLD", "100")),
        genetic_light_generations=int(os.getenv("GENETIC_LIGHT_GENERATIONS", "10")),
        genetic_light_mutation_probability=float(os.getenv("GENETIC_LIGHT_MUTATION_PROBABILITY", "0.2")),
        genetic_light_population=int(os.getenv("GENETIC_LIGHT_POPULATION", "10")),
        genetic_heavy_generations=int(os.getenv("GENETIC_HEAVY_GENERATIONS", "40")),
        genetic_heavy_mutation_probability=float(os.getenv("GENETIC_HEAVY_MUTATION_PROBABILITY", "0.2")),
        genetic_heavy_population=int(os.getenv("GENETIC_HEAVY_POPULATION", "30")),
        algo_decider_branch_and_bound_max_items=int(os.getenv("ALGO_DECIDER_BRANCH_AND_BOUND_MAX_ITEMS", "15")),
        algo_decider_dynamic_programming_max_iterations=int(
            os.getenv("ALGO_DECIDER_DYNAMIC_PROGRAMMING_MAX_ITERATIONS", "10000")
        ),
        subscription_backend_base_url=os.getenv("SUBSCRIPTION_BACKEND_BASE_URL"),
    )


def get_solver_loader(config: Config = get_config()):
    return SolverLoader(config)


def get_algorithm_runner(solver_loader=get_solver_loader()) -> AlgorithmRunner:
    return AlgorithmRunner(solver_loader)


def get_rabbit_channel_context(config: Config = get_config()) -> RabbitChannelContext:
    return RabbitChannelContext(config.rabbit_connection_params)


async def get_rabbit_channel_api(config: Config = Depends(get_config)) -> aio_pika.abc.AbstractChannel:
    ctx = RabbitChannelContext(config.rabbit_connection_params)
    async with ctx as channel:
        yield channel


def get_solver_router_producer_api(
    rabbit_channel: aio_pika.abc.AbstractChannel = Depends(get_rabbit_channel_api), config: Config = Depends(get_config)
) -> SolverRouterProducer:
    return SolverRouterProducer(rabbit_channel, config.solver_queue)


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


def get_subscriptions_service(config: Config = Depends(get_config)) -> SubscriptionsService:
    client = AsyncClient(base_url=config.subscription_backend_base_url)
    return SubscriptionsService(client)


def get_cluster_availability_service_api(
    rabbit_channel: aio_pika.abc.AbstractChannel = Depends(get_rabbit_channel_api), config: Config = Depends(get_config)
) -> ClusterAvailabilityService:
    return ClusterAvailabilityService(rabbit_channel, config)


def get_algorithm_decider_api(
    subscriptions_service: SubscriptionsService = Depends(get_subscriptions_service),
    cluster_availability_service: ClusterAvailabilityService = Depends(get_cluster_availability_service_api),
    config: Config = Depends(get_config),
) -> AlgorithmDecider:
    return AlgorithmDecider(
        subscriptions_service,
        cluster_availability_service,
        config.algo_decider_branch_and_bound_max_items,
        config.algo_decider_dynamic_programming_max_iterations,
    )


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
    request: RouterSolveRequest,
    redis: Redis = Depends(get_redis_api),
    config: Config = Depends(get_config),
) -> SolutionReportWaiter:
    return SolutionReportWaiter(
        redis, config.solutions_channel_prefix, request.knapsack_id, config.wait_for_report_timeout_seconds
    )


def get_solver_consumer(
    rabbit_channel_context=get_rabbit_channel_context(),
    algo_runner=get_algorithm_runner(),
    claims_service=get_claims_service(),
    solution_reporter=get_solution_reporter(),
    suggested_solution_service=get_suggested_solutions_service(),
) -> SolverInstanceConsumer:
    return SolverInstanceConsumer(
        rabbit_channel_context, algo_runner, claims_service, solution_reporter, suggested_solution_service
    )


def get_solution_maintainer(
    suggested_solution_service: SuggestedSolutionsService = get_suggested_solutions_service(),
    redis_client: Redis = get_redis(),
    time_service: TimeService = get_time_service(),
    claims_service: ClaimsService = get_claims_service(),
    config: Config = get_config(),
) -> SolutionMaintainer:
    return SolutionMaintainer(suggested_solution_service, redis_client, time_service, claims_service, config)
