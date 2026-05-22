import json
import re
from bs4 import BeautifulSoup

from .schemas import Price


def parse_metadata(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    # JSON-LD 우선
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "Product"), {})
            if data.get("@type") == "Product":
                result["name"] = data.get("name")
                result["brand"] = _extract_brand(data)
                result["category"] = data.get("category")
                result["main_image_url"] = _extract_image(data)
                result["price"] = _extract_price_from_ld(data)
                result["rating"] = _extract_rating(data)
                result["review_count"] = _extract_review_count(data)
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    # Open Graph fallback
    if not result.get("name"):
        og_title = soup.find("meta", property="og:title")
        if og_title:
            result["name"] = og_title.get("content", "").strip()

    if not result.get("main_image_url"):
        og_image = soup.find("meta", property="og:image")
        if og_image:
            result["main_image_url"] = og_image.get("content", "")

    return result


def _extract_brand(data: dict) -> str | None:
    brand = data.get("brand")
    if isinstance(brand, dict):
        return brand.get("name")
    if isinstance(brand, str):
        return brand
    return None


def _extract_image(data: dict) -> str | None:
    image = data.get("image")
    if isinstance(image, list) and image:
        img = image[0]
        return img.get("url") if isinstance(img, dict) else img
    if isinstance(image, dict):
        return image.get("url")
    if isinstance(image, str):
        return image
    return None


def _extract_price_from_ld(data: dict) -> Price:
    offers = data.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    price_val = offers.get("price") or offers.get("lowPrice")
    try:
        sale = int(float(str(price_val).replace(",", ""))) if price_val else None
    except (ValueError, TypeError):
        sale = None

    return Price(sale=sale)


def _extract_rating(data: dict) -> float | None:
    agg = data.get("aggregateRating", {})
    val = agg.get("ratingValue") if isinstance(agg, dict) else None
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _extract_review_count(data: dict) -> int | None:
    agg = data.get("aggregateRating", {})
    val = agg.get("reviewCount") or agg.get("ratingCount") if isinstance(agg, dict) else None
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def extract_product_id(url: str) -> str:
    match = re.search(r"/products/(\d+)", url)
    if match:
        return match.group(1)
    # brand.naver.com 형식
    match = re.search(r"/(\d+)(?:\?|$)", url)
    if match:
        return match.group(1)
    return url.split("/")[-1].split("?")[0]
