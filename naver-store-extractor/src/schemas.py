from datetime import datetime
from pydantic import BaseModel


class Price(BaseModel):
    original: int | None = None
    sale: int | None = None
    currency: str = "KRW"


class ProductDetails(BaseModel):
    features: list[str] = []
    ingredients: list[str] | None = None
    effects: list[str] | None = None
    specs: dict[str, str] = {}
    usage: str | None = None
    storage: str | None = None
    caution: str | None = None


class Product(BaseModel):
    url: str
    product_id: str
    name: str
    brand: str | None = None
    category: str | None = None
    price: Price
    rating: float | None = None
    review_count: int | None = None
    main_image_url: str | None = None
    details: ProductDetails
    extracted_at: datetime
    source_screenshots: list[str] = []
