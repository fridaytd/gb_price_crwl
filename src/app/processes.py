from datetime import datetime


from typing import Final

from pydantic import ValidationError

from app import config

from .gameboost.crwl import extract_page_data
from .gameboost.models import Offer, PageData
from .sheet.models import RowRun
from . import logger
from .shared.decorators import retry_on_fail
from .utils import sleep_for

DEFAULT_RELAX_TIME: Final[float] = 5


def platten_offer(page_data: PageData) -> list[Offer]:
    offers: list[Offer] = []

    model = page_data.props.model

    if model.currency_offer:
        offers.append(model.currency_offer)

    if model.currencies:
        offers.extend(model.currencies.data)

    if model.account_offer:
        offers.append(model.account_offer)

    if model.accounts:
        offers.extend(model.accounts.data)

    if model.item_offer:
        offers.append(model.item_offer)

    if model.items:
        offers.extend(model.items.data)

    return offers


def is_valid_offer(
    offer: Offer,
    run_row: RowRun,
    blacklist: list[str],
) -> bool:
    if offer.seller.username in blacklist:
        return False

    if offer.seller.total_ratings < run_row.FEEDBACK_QTY:
        return False

    if offer.seller.rating.value < run_row.FEEDBACK_PERCENT:
        return False

    if offer.delivery_time.seconds // 60 > run_row.DELIVERY_TIME:
        return False

    if offer.min_quantity and offer.min_quantity > run_row.MIN_QTY:
        return False

    if offer.stock and offer.stock < run_row.STOCK1:
        return False

    return True


def filter_offers_and_our_offer(
    offers: list[Offer],
    run_row: RowRun,
) -> tuple[list[Offer], Offer | None]:
    blacklist: list[str] = run_row.get_blacklist()
    valid_offers: list[Offer] = []
    my_offer: Offer | None = None

    for offer in offers:
        if offer.seller.username == config.OUR_SELLER_NAME:
            my_offer = offer

        if is_valid_offer(offer=offer, run_row=run_row, blacklist=blacklist):
            valid_offers.append(offer)

    return valid_offers, my_offer


def find_min_valid_offer(
    valid_offers: list[Offer],
) -> Offer:
    min_offer: Offer = valid_offers[0]
    for offer in valid_offers:
        if offer.price.amount < min_offer.price.amount:
            min_offer = offer

    return min_offer


def __get_offer_price(
    offer: Offer,
) -> float:
    return offer.price.amount


def find_my_offer_top(
    offers: list[Offer],
) -> int:
    sorted_offers = sorted(offers, key=lambda x: __get_offer_price(x))

    for i, offer in enumerate(sorted_offers):
        if offer.seller.username == config.OUR_SELLER_NAME:
            return i + 1

    return -1


def last_update_message(
    now: datetime,
) -> str:
    formatted_date = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted_date


@retry_on_fail(max_retries=3, sleep_interval=1)
def run(sb, index: int) -> None:
    try:
        logger.info(f"Processing row: {index}")
        run_row = RowRun.get(
            sheet_id=config.SPREADSHEET_KEY, sheet_name=config.SHEET_NAME, index=index
        )

        page_data = extract_page_data(sb, run_row.PRODUCT_COMPARE)

        offers = platten_offer(page_data)

        valid_offers, my_offer = filter_offers_and_our_offer(offers, run_row)

        run_row.Note = ""

        if len(valid_offers) > 0:
            min_offer = find_min_valid_offer(valid_offers)
            logger.info(f"Min offer: {min_offer}")
            run_row.SELLER = min_offer.seller.username
            run_row.LOWEST_PRICE_EUR = str(min_offer.price.amount)
            run_row.LOWEST_PRICE_USD = str(min_offer.local_price.amount)

        else:
            logger.info("No valid offer")
            run_row.SELLER = ""
            run_row.LOWEST_PRICE_EUR = ""
            run_row.LOWEST_PRICE_USD = ""
            run_row.Note = run_row.Note + "Không có seller hợp lệ \n"

        if my_offer:
            my_top = find_my_offer_top(offers)
            logger.info(f"My offer at top {my_top}")
            run_row.Top = str(my_top)
            run_row.CNLGAMING_EUR = str(my_offer.price.amount)
            run_row.CNLGAMING_USD = str(my_offer.local_price.amount)

        else:
            logger.info("Can't find my offer")
            run_row.Top = "NaN"
            run_row.CNLGAMING_EUR = ""
            run_row.CNLGAMING_USD = ""
            run_row.Note = (
                run_row.Note + f"Không tìm thấy seller {config.OUR_SELLER_NAME}"
            )

        run_row.Time_update = last_update_message(datetime.now())
        run_row.update()
        sleep_for(run_row.RELAX)

    except ValidationError as e:
        logger.exception(f"VALIDATION ERROR AT ROW: {index}")
        logger.exception(e.errors())
        RowRun.update_note_message(
            sheet_id=config.SPREADSHEET_KEY,
            sheet_name=config.SHEET_NAME,
            index=index,
            messages=f"{last_update_message(datetime.now())} VALIDATION ERROR AT ROW: {index}",
        )
        sleep_for(DEFAULT_RELAX_TIME)

    except Exception as e:
        logger.exception(f"FAILED AT ROW: {index}")
        logger.exception(e)
        RowRun.update_note_message(
            sheet_id=config.SPREADSHEET_KEY,
            sheet_name=config.SHEET_NAME,
            index=index,
            messages=f"{last_update_message(datetime.now())} FAILED AT ROW: {index}",
        )
        sleep_for(DEFAULT_RELAX_TIME)
