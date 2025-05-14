from pydantic import BaseModel


class SellerRating(BaseModel):
    value: float
    amount: float
    format: str


class Seller(BaseModel):
    id: int
    username: str
    rating: SellerRating
    total_ratings: int


class Currency(BaseModel):
    symbol: str
    code: str


class Price(BaseModel):
    amount: float
    currency: str | Currency


class DeliveryTime(BaseModel):
    seconds: int


class Offer(BaseModel):
    id: int
    seller: Seller
    price: Price
    local_price: Price
    stock: int | None = None
    min_quantity: int | None = None
    delivery_time: DeliveryTime


class CurrentPageData(BaseModel):
    current_page: int
    data: list[Offer]


class Model(BaseModel):
    currency_offer: Offer | None = None
    currencies: CurrentPageData | None = None
    item_offer: Offer | None = None
    items: CurrentPageData | None = None
    account_offer: Offer | None = None
    accounts: CurrentPageData | None = None


class Props(BaseModel):
    model: Model


class PageData(BaseModel):
    props: Props
