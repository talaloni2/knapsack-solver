import json

import pytest
from aioredis import Redis
from aioredis.client import PubSub
from pytest_mock import MockerFixture

from component_factory import get_solution_reporter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.solution import SolutionReport, SolutionReportCause, AlgorithmSolution
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_solution_reporter_report_suggestion(
    redis_subscriber: PubSub,
    redis_client: Redis,
    knapsack_id: str,
    solution_suggestions_service: SuggestedSolutionsService,
    mocker: MockerFixture,
    config: Config,
):
    register_solution_spy = mocker.spy(solution_suggestions_service, "register_suggested_solutions")
    solution_reporter = get_solution_reporter(config=config, suggested_solutions_service=solution_suggestions_service)
    expected_solutions = [AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), value=1, volume=1)])]
    expected_response = SolutionReport(cause=SolutionReportCause.SOLUTION_FOUND)

    await solution_reporter.report_solution_suggestions(expected_solutions, knapsack_id)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))
    suggested_solution = await solution_suggestions_service.get_solutions(knapsack_id)
    solutions_without_ids = [s for s in suggested_solution.solutions.values()]

    assert expected_response == response
    assert expected_solutions == solutions_without_ids
    register_solution_spy.assert_called_once_with(expected_solutions, knapsack_id)


@pytest.mark.asyncio
async def test_solution_reporter_report_error(
    redis_subscriber: PubSub,
    redis_client: Redis,
    knapsack_id: str,
    solution_suggestions_service: SuggestedSolutionsService,
    mocker: MockerFixture,
    config: Config,
):
    register_solution_spy = mocker.spy(solution_suggestions_service, "register_suggested_solutions")
    solution_reporter = get_solution_reporter(config=config, suggested_solutions_service=solution_suggestions_service)
    expected_response = SolutionReport(cause=SolutionReportCause.NO_ITEM_CLAIMED)

    await solution_reporter.report_error(knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))
    suggested_solution = await solution_suggestions_service.get_solutions(knapsack_id)

    assert expected_response == response
    assert suggested_solution is None
    register_solution_spy.assert_not_called()
