import asyncio

import uvicorn

import server
from component_factory import get_solver_consumer, get_solution_maintainer, get_config
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.solution_maintainer import run_tasks
from models.config.configuration import Config, DeploymentType


def main(config: Config):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if config.deployment_type == DeploymentType.ROUTER:
        uvicorn.run(app=server.app, host="0.0.0.0", port=config.server_port)
        return
    if config.deployment_type == DeploymentType.SOLVER:
        consumer = get_solver_consumer()
        loop.run_until_complete(start_solver_consumer(consumer, config.solver_queue))
        return
    if config.deployment_type == DeploymentType.MAINTAINER:
        maintainer = get_solution_maintainer()
        loop.run_until_complete(run_tasks(maintainer))
        loop.run_forever()


async def start_solver_consumer(consumer: SolverInstanceConsumer, queue_name: str):
    async with consumer:
        await consumer.start_consuming(queue_name)


if __name__ == "__main__":
    main(get_config())
