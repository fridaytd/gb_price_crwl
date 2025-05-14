import random

from bs4 import BeautifulSoup
from .models import PageData
from .exceptions import CrwlError
from . import logger


def get_soup(sb, url: str) -> BeautifulSoup:
    logger.info(f"Get soup for url: {url}")
    sb.get(url)
    sb.cdp.sleep(random.uniform(0.5, 0.9))
    soup = BeautifulSoup(sb.cdp.get_page_source(), "html.parser")
    sb.cdp.sleep(random.uniform(0.3, 0.7))
    return soup


def extract_page_data(sb, url: str) -> PageData:
    soup = get_soup(sb, url)
    app_tag = soup.select_one("#app")

    if not app_tag:
        raise CrwlError("App tag not found!!!")

    page_data = app_tag.attrs.get("data-page", None)
    if not page_data:
        raise CrwlError("Page data not found!!!")

    # with open("data.json", "w") as f:
    #     json.dump(json.loads(page_data), f)

    return PageData.model_validate_json(str(page_data))
