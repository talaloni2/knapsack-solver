from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from logic.algorithm_decider import AlgorithmDecider, get_algorithm_decider
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest, RouterResolveResponse

router = APIRouter()


@router.post("/solve")
async def route_solve(
    request: RouterSolveRequest,
    algorithm_decider: AlgorithmDecider = Depends(get_algorithm_decider),
) -> RouterResolveResponse:
    requested_algorithm = await algorithm_decider.decide()
    if requested_algorithm != Algorithms.FIRST_FIT:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unsupported algorithm chosen",
        )
    items = _get_first_fit_item(request)
    return RouterResolveResponse(items=items, knapsack_id=request.knapsack_id)


def _get_first_fit_item(request: RouterSolveRequest) -> list[KnapsackItem]:
    return [next(item for item in request.items if item.volume <= request.volume)]
