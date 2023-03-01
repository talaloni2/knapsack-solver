from fastapi import APIRouter, Depends

from logic.algorithm_decider import AlgorithmDecider, get_algorithm_decider
from models.knapsack_router_dto import RouterSolveRequest, RouterResolveResponse

router = APIRouter()


@router.post("/solve")
async def route_solve(
    request: RouterSolveRequest,
    algorithm_decider: AlgorithmDecider = Depends(get_algorithm_decider),
) -> RouterResolveResponse:
    requested_algorithm = await algorithm_decider.decide()
    return RouterResolveResponse(
        items=[request.items[0]] if request.items else [],
        knapsack_id=request.knapsack_id,
    )
