from fastapi import APIRouter, Depends

from component_factory import get_solver_router_producer, get_algorithm_decider, get_suggested_solutions_service_api
from logic.algorithm_decider import AlgorithmDecider
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.suggested_solution_service import SuggestedSolutionsService
from models.knapsack_router_dto import (
    RouterSolveRequest,
    RouterResolveResponse,
    AcceptSolutionRequest,
    AcceptSolutionResponse,
    RejectSolutionResponse,
    RejectSolutionsRequest,
)
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult

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


@router.post("/accept-solution")
async def accept_solution(
    request: AcceptSolutionRequest,
    suggested_solution_service: SuggestedSolutionsService = Depends(get_suggested_solutions_service_api),
) -> AcceptSolutionResponse:
    solution_exists = await suggested_solution_service.is_solution_exists(request.knapsack_id, request.solution_id)
    if not solution_exists:
        return AcceptSolutionResponse(result=AcceptResult.SOLUTION_NOT_EXISTS)

    result = await suggested_solution_service.accept_suggested_solution(request.knapsack_id, request.solution_id)
    return AcceptSolutionResponse(result=result)


@router.post("/reject-solutions")
async def reject_solutions(
    request: RejectSolutionsRequest,
    suggested_solution_service: SuggestedSolutionsService = Depends(get_suggested_solutions_service_api),
) -> RejectSolutionResponse:
    solution_exists = bool(await suggested_solution_service.get_solutions(request.knapsack_id))
    if not solution_exists:
        return RejectSolutionResponse(result=RejectResult.SUGGESTION_NOT_EXISTS)

    result = await suggested_solution_service.reject_suggested_solutions(request.knapsack_id)
    return RejectSolutionResponse(result=result)
