from enum import Enum
from typing import NamedTuple

from models.config.rabbit_connection_params import RabbitConnectionParams
from models.config.redis_connection_params import RedisConnectionParams


class DeploymentType(str, Enum):
    ROUTER = "router"
    SOLVER = "solver"
    MAINTAINER = "maintainer"


class Config(NamedTuple):
    server_port: int
    deployment_type: DeploymentType

    rabbit_connection_params: RabbitConnectionParams
    redis_connection_params: RedisConnectionParams

    solver_queue: str

    items_claim_hash: str
    suggested_solutions_claims_hash: str
    running_knapsack_claims_hash: str

    solutions_channel_prefix: str
    wait_for_report_timeout_seconds: float
    suggested_solutions_hash: str
    accepted_solutions_list: str

    clean_old_suggestion_interval_seconds: int
    clean_old_accepted_solutions_interval_seconds: int
    suggestion_ttl_seconds: int
    accepted_solution_ttl_seconds: int
    accepted_solutions_prefect_count: int

    solvers_moderate_busy_threshold: int
    solvers_busy_threshold: int
    solvers_very_busy_threshold: int
