from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from config import ISTHEREANYDEAL_API_KEY
from utils.pagination import PaginatedResult


class Assets(BaseModel):
    boxart: str
    banner145: str


class Shop(BaseModel):
    id: int
    name: str


class Platform(BaseModel):
    id: int
    name: str


class Price(BaseModel):
    amount: float
    currency: str


class Deal(BaseModel):
    shop: Shop
    url: str
    platforms: list[Platform]
    price: Price
    voucher: str | None


class ItemType(Enum):
    DLC = "dlc"
    GAME = "game"


class DealItem(BaseModel):
    id: UUID
    title: str
    type: ItemType | None
    mature: bool
    deal: Deal


def build_deals_url(offset: int = 0) -> str:
    return f"https://api.isthereanydeal.com/deals/v2?sort=price&offset={offset}&key={ISTHEREANYDEAL_API_KEY}"


class IsThereAnyDealDealsList(PaginatedResult[DealItem]):
    model_config = ConfigDict(alias_generator=to_camel)

    next_offset: int
    has_more: bool
    items: list[DealItem] = Field(alias="list")

    def get_has_more(self) -> bool:
        return self.has_more

    def get_next_url(self) -> str:
        return build_deals_url(self.next_offset)

    def get_items(self) -> list[DealItem]:
        return self.items
