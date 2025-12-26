from fastapi import FastAPI

from isthereanydeal.deals_list import DealItem
from isthereanydeal.giveaways import get_current_giveaways

app = FastAPI()


@app.get("/")
async def hello_world() -> dict:
    return {"message": "Hello World"}


@app.get("/api/v1/isthereanydeal/current-giveaways")
async def current_giveaways() -> list[DealItem]:
    return get_current_giveaways()
