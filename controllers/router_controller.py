from fastapi import APIRouter, Depends

from component_factory import get_solver_router_producer, get_algorithm_decider
from logic.algorithm_decider import AlgorithmDecider
from logic.producer.solver_router_producer import SolverRouterProducer
from models.knapsack_router_dto import RouterSolveRequest, RouterResolveResponse
from models.knapsack_solver_instance_dto import SolverInstanceRequest

router = APIRouter()


@router.post("/solve")
async def route_solve(
    request: RouterSolveRequest,
    algorithm_decider: AlgorithmDecider = Depends(get_algorithm_decider),
    solve_request_producer: SolverRouterProducer = Depends(get_solver_router_producer),
) -> RouterResolveResponse:
    requested_algorithm = await algorithm_decider.decide()
    solver_instance_request = SolverInstanceRequest(
        items=request.items, volume=request.volume, knapsack_id=request.knapsack_id, algorithm=requested_algorithm
    )
    async with solve_request_producer:
        await solve_request_producer.produce_solver_instance_request(solver_instance_request)
    return RouterResolveResponse(
        items=[request.items[0]] if request.items else [],
        knapsack_id=request.knapsack_id,
    )
