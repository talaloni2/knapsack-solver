import http
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from component_factory import (
    get_solver_router_producer_api,
    get_algorithm_decider_api,
    get_suggested_solutions_service_api,
    get_solution_report_waiter_api_route_solve,
    get_claims_service_api,
    get_config,
)
from logger import logger
from logic.algorithm_decider import AlgorithmDecider
from logic.claims_service import ClaimsService
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solution_report_waiter import SolutionReportWaiter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.config.configuration import Config
from models.knapsack_router_dto import (
    RouterSolveRequest,
    AcceptSolutionRequest,
    AcceptSolutionResponse,
    RejectSolutionResponse,
    RejectSolutionsRequest,
    ItemClaimedResponse,
)
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.solution import SolutionReport, SolutionReportCause, SuggestedSolution
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult

router = APIRouter()


@router.post("/solve")
async def route_solve(
    request: RouterSolveRequest,
    algorithm_decider: AlgorithmDecider = Depends(get_algorithm_decider_api),
    solve_request_producer: SolverRouterProducer = Depends(get_solver_router_producer_api),
    solution_reports_waiter: SolutionReportWaiter = Depends(get_solution_report_waiter_api_route_solve),
    suggested_solution_service: SuggestedSolutionsService = Depends(get_suggested_solutions_service_api),
    config: Config = Depends(get_config),
) -> SuggestedSolution:
    if not request.items:
        logger.info(f"Got no items request for {request.knapsack_id}. Aborting.")
        return await no_items_claimed_response()
    solver_instance_request: SolverInstanceRequest = await _generate_solve_request(algorithm_decider, request)

    async with solution_reports_waiter, solve_request_producer:
        await solve_request_producer.produce_solver_instance_request(solver_instance_request)
        report: SolutionReport = await solution_reports_waiter.wait_for_solution_report()

    if report.cause == SolutionReportCause.NO_ITEM_CLAIMED:
        logger.info(f"Could not claim any items for {request.knapsack_id}. Given items: {request.items}")
        return await no_items_claimed_response()
    if report.cause != SolutionReportCause.SOLUTION_FOUND:
        # noinspection PyTypeChecker
        logger.warn(f"Failed solving due to: {report.cause}")
        return _generate_solve_fail_error_response(report)

    res = await suggested_solution_service.get_solutions(request.knapsack_id)
    res.solutions = {sol_id: sol for sol_id, sol in res.solutions.items() if sol.items}
    res = add_expiry(res, config.suggestion_ttl_seconds)
    return res


def add_expiry(res: SuggestedSolution, suggestion_ttl_seconds: int):
    res.expires_at = res.time + timedelta(seconds=suggestion_ttl_seconds)
    return res


async def no_items_claimed_response():
    return JSONResponse(
        status_code=http.HTTPStatus.NO_CONTENT,
        content=None
    )


async def _generate_solve_request(
    algorithm_decider: AlgorithmDecider, request: RouterSolveRequest
) -> SolverInstanceRequest:
    requested_algorithms = await algorithm_decider.decide(request.knapsack_id, len(request.items), request.volume)
    solver_instance_request = SolverInstanceRequest(
        items=request.items, volume=request.volume, knapsack_id=request.knapsack_id, algorithms=requested_algorithms
    )
    return solver_instance_request


def _generate_solve_fail_error_response(report: SolutionReport) -> JSONResponse:
    is_timeout = report.cause == SolutionReportCause.TIMEOUT
    return JSONResponse(
        status_code=http.HTTPStatus.GATEWAY_TIMEOUT if is_timeout else http.HTTPStatus.BAD_REQUEST,
        content={"message": "Could not resolve request, please retry with different parameters", "cause": report.cause},
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


@router.get("/check-claimed/{item_id}")
async def is_item_claimed(item_id: str, claims_service: ClaimsService = Depends(get_claims_service_api)):
    return ItemClaimedResponse(is_claimed=await claims_service.is_item_claimed(item_id))
