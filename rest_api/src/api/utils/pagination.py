from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

import requests
from pydantic import BaseModel

V = TypeVar("V")


class PaginatedResult[I](BaseModel, ABC):
    @abstractmethod
    def get_has_more(self) -> bool:
        pass

    @abstractmethod
    def get_next_url(self) -> str:
        pass

    @abstractmethod
    def get_items(self) -> list[I]:
        pass


T = TypeVar("T", bound=PaginatedResult)


def follow_pagination(
    initial_url: str,
    paginated_result_class: type[T],
    *,
    should_continue: Callable[[T], bool] = lambda _: True,
    is_valid: Callable[[V], bool] = lambda _: True,
) -> list[V]:
    results: list[V] = []
    session = requests.session()
    response = session.get(initial_url)
    response.raise_for_status()
    result = paginated_result_class.model_validate(response.json())
    results.extend([item for item in result.get_items() if is_valid(item)])
    while result.get_has_more() and should_continue(result):
        response = session.get(result.get_next_url())
        response.raise_for_status()
        result = paginated_result_class.model_validate(response.json())
        results.extend([item for item in result.get_items() if is_valid(item)])
    return results
