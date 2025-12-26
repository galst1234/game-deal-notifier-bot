from isthereanydeal.deals_list import DealItem, IsThereAnyDealDealsList, build_deals_url
from utils.pagination import follow_pagination


def get_current_giveaways() -> list[DealItem]:
    return follow_pagination(
        initial_url=build_deals_url(),
        paginated_result_class=IsThereAnyDealDealsList,
        should_continue=lambda result: result.items[-1].deal.price.amount == 0,
        is_valid=lambda item: item.deal.price.amount == 0,
    )
