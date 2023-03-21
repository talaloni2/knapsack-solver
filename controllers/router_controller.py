import http
import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from component_factory import (
    get_solver_router_producer,
    get_algorithm_decider,
    get_suggested_solutions_service_api,
    get_solution_report_waiter_api_route_solve,
)
from logic.algorithm_decider import AlgorithmDecider
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solution_report_waiter import SolutionReportWaiter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.knapsack_router_dto import (
    RouterSolveRequest,
    AcceptSolutionRequest,
    AcceptSolutionResponse,
    RejectSolutionResponse,
    RejectSolutionsRequest,
)
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.solution import SolutionReport, SolutionReportCause, SuggestedSolution
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult

router = APIRouter()


@router.post("/solve")
async def route_solve(
    request: RouterSolveRequest,
    algorithm_decider: AlgorithmDecider = Depends(get_algorithm_decider),
    solve_request_producer: SolverRouterProducer = Depends(get_solver_router_producer),
    solution_reports_waiter: SolutionReportWaiter = Depends(get_solution_report_waiter_api_route_solve),
    suggested_solution_service: SuggestedSolutionsService = Depends(get_suggested_solutions_service_api),
) -> SuggestedSolution:
    solver_instance_request: SolverInstanceRequest = await _generate_solve_request(algorithm_decider, request)

    async with solution_reports_waiter, solve_request_producer:
        await solve_request_producer.produce_solver_instance_request(solver_instance_request)
        report: SolutionReport = await solution_reports_waiter.wait_for_solution_report()

    if report.cause != SolutionReportCause.SOLUTION_FOUND:
        # noinspection PyTypeChecker
        return _generate_solve_fail_error_response(report)

    res = await suggested_solution_service.get_solutions(request.knapsack_id)
    return res


async def _generate_solve_request(
    algorithm_decider: AlgorithmDecider, request: RouterSolveRequest
) -> SolverInstanceRequest:
    requested_algorithm = await algorithm_decider.decide()
    solver_instance_request = SolverInstanceRequest(
        items=request.items, volume=request.volume, knapsack_id=request.knapsack_id, algorithm=requested_algorithm
    )
    return solver_instance_request


def _generate_solve_fail_error_response(report: SolutionReport) -> JSONResponse:
    is_internal_error = report.cause == SolutionReportCause.TIMEOUT
    return JSONResponse(
        status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR if is_internal_error else http.HTTPStatus.BAD_REQUEST,
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
