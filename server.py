from fastapi import FastAPI

from controllers.router_controller import router as router_controller_router

app = FastAPI()

app.include_router(router_controller_router, prefix="/knapsack-router")
