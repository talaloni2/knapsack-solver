import os

from fastapi import Depends

from logic.algorithm_decider import AlgorithmDecider
from logic.algorithm_runner import AlgorithmRunner
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solver.solver_loader import SolverLoader
from models.rabbit_connection_params import RabbitConnectionParams


def get_rabbit_connection_params() -> RabbitConnectionParams:
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return RabbitConnectionParams(host=host, port=port, user=user, password=password)


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
