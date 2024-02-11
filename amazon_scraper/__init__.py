from parsel import Selector, SelectorList
from pydantic import validate_call
from typing import Optional
import random
import httpx
import re

from .settings import DEFAULT_ORIGIN_URL, DEFAULT_CURRENCY_SYMBOL
from ._utils.url import parse_url

validate_config = dict(arbitrary_types_allowed = True)

@validate_call(config = validate_config)
def parse_title(selector_list: SelectorList[Selector]) -> str:
    raw_text = selector_list.css("::text").get()

    if raw_text:
        parsed_title = raw_text.strip()
        return parsed_title

@validate_call(config = validate_config)
def parse_current_price(selector_list: Optional[SelectorList[Selector]], currency_symbol: str) -> float:
    if len(selector_list) <= 0: return

    raw_text = selector_list.css("::text").get()

    if raw_text:
        parsed_price = int(
            float(raw_text
                .replace(currency_symbol, "")
                .replace(".", "")
                .replace(",", ".")
            ) * 1000
        )

        return parsed_price

parse_price_before_discount = parse_current_price

@validate_call(config = validate_config)
def parse_description(selector_list: Optional[SelectorList[Selector]]) -> Optional[str]:
    if len(selector_list) <= 0: return

    element_id = selector_list.css("::attr(id)").get()

    description = ""

    if element_id == "bookDescription_feature_div":
        description = "\n".join(selector_list.css("p::text").getall())

    elif element_id == "feature-bullets":
        description = "\n- ".join(selector_list.css("li::text").getall())
    
    return description

@validate_call(config = validate_config)
def parse_rating(selector_list: SelectorList[Selector]) -> float:
    raw_text = selector_list.css("::text").get()

    if raw_text:
        rating = float(raw_text.replace(",", "."))
        return rating

@validate_call(config = validate_config)
def parse_specifications(selector_list: SelectorList[Selector]) -> dict:
    specifications = {}

    if len(selector_list) > 0:
        span_tags = selector_list.css("span")
        key = span_tags[0].xpath("string()").get().lower()
        value = span_tags[1].xpath("string()").get()
        specifications[key] = value

    return specifications

@validate_call
def parse_results(selector_list: SelectorList[Selector]) -> dict:
    ...

@validate_call
def parse_current_page(selector_list: SelectorList[Selector]) -> int: ...

class Amazon:
    _referer_urls = [
        "https://www.google.com/search?q=amazon",
        "https://www.amazon.com.br/s?k=livros&__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3IGH1VN1GR9CE&sprefix=livros%2Caps%2C240&ref=nb_sb_noss_1",
        "https://www.amazon.com.br/Pr%C3%ADncipe-Maquiavel-Acompanha-marcador-p%C3%A1ginas/dp/6584956199/ref=sr_1_11?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3IGH1VN1GR9CE&keywords=livros&qid=1707609465&sprefix=livros%2Caps%2C240&sr=8-11",
        "https://www.amazon.com.br/Apple-iPhone-13-128-GB-das-estrelas/dp/B09T4YK6QK/ref=sr_1_1_sspa?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=38E6W5UZMGKIB&keywords=celulares&qid=1707609515&sprefix=cel%2Caps%2C714&sr=8-1-spons&ufe=app_do%3Aamzn1.fos.25548f35-0de7-44b3-b28e-0f56f3f96147&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1",
        "https://www.amazon.com.br/Smartphone-Xiaomi-Powerful-Snapdragon%C2%AE-performance/dp/B0CT922MHL/ref=sr_1_17?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=38E6W5UZMGKIB&keywords=celulares&qid=1707609515&sprefix=cel%2Caps%2C714&sr=8-17&ufe=app_do%3Aamzn1.fos.25548f35-0de7-44b3-b28e-0f56f3f96147"
    ]
    
    @validate_call
    def __init__(
        self,
        origin_url: str = DEFAULT_ORIGIN_URL,
        currency_symbol: str = DEFAULT_CURRENCY_SYMBOL,
        proxy: Optional[tuple[str, str, int]] = None
    ) -> None:
        self._origin_url = origin_url.removesuffix("/")
        self._currency_symbol = currency_symbol
        self._referer_urls.append(self._origin_url)
        self._proxy = proxy if not proxy else f"{proxy[0]}://{proxy[1]}:{proxy[2]}"

        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "device-memory": "8",
            "downlink": "10",
            "dpr": "1",
            "ect": "4g",
            "pragma": "no-cache",
            "rtt": "50",
            "sec-ch-device-memory": "8",
            "sec-ch-dpr": "1",
            "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"10.0.0\"",
            "sec-ch-viewport-width": "996",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "viewport-width": "996",
            "referer": random.choice(self._referer_urls)
        }

    @classmethod
    @validate_call
    def _fetch(
        cls,
        url: str,
        proxy: Optional[str] = None,
        params: dict = {},
        headers: dict = {},
    ) -> httpx.Response:
        response = httpx.get(
            url = url,
            headers = headers,
            params = params,
            proxy = proxy
        )

        with open("response.html", "w", encoding = "utf-8") as file:
            file.write(response.text)

        if response.status_code != 200:
            raise httpx.HTTPStatusError(
                message = f"An error occurred when trying to make this request, the server returned a status code of '{response.status_code}'!",
                request = response.request,
                response = response
            )

        return response

    @validate_call
    def scrape_product(self, url: str) -> dict:
        item_id, item_slug = parse_url(url, self._origin_url)

        if item_id is None:
            raise ValueError(f"Not found item id from '{url}'")

        if item_slug is None:
            item_url = f"{self._origin_url}/dp/{item_id}/"
        else:
            item_url = f"{self._origin_url}/{item_slug}/dp/{item_id}/"

        response = self._fetch(
            url = item_url,
            headers = self._headers,
            proxy = self._proxy
        )

        # with open("response.html", "r", encoding = "utf-8") as file:
        #     html_text = file.read()

        html_text = response.text
        selector = Selector(html_text)

        title_selector = selector.css("#productTitle")
        current_price_selector = selector.css("#price") or selector.css("#corePrice_feature_div .a-offscreen")
        price_before_discount_selector = selector.css("#listPrice") or selector.css(".a-price")
        description_selector = selector.css("#bookDescription_feature_div") or selector.css("#feature-bullets") or selector.css("#drengr_desktopTabbedDescriptionOverviewContent_feature_div")
        rating_selector = selector.css("#averageCustomerReviews_feature_div .a-color-base")
        specifications_selector = selector.css("tr.a-spacing-small")

        return {
            "id": item_id,
            "slug": item_slug,
            "title": parse_title(title_selector),
            "current_price": parse_current_price(current_price_selector, self._currency_symbol),
            "price_before_discount": parse_price_before_discount(price_before_discount_selector, self._currency_symbol),
            "description": parse_description(description_selector),
            "extra": {
                "image_sources": re.findall('"hiRes":"(.+?)"', html_text),
                "rating": parse_rating(rating_selector),
                "specifications": parse_specifications(specifications_selector)
            }
        }


    @validate_call
    def scrape_search(
        self,
        query: str,
        page_number: int = 1
    ) -> dict:
        params = {
            "ref": f"sr_pg_{page_number}",
            "k": query
        }

        url = f"{self._origin_url}/s"
        response = self._fetch(url, params = params)

        html_text = response.text
        selector = Selector(html_text)

        current_page_selector = selector.css(".s-pagination-selected")
        last_page_selector = selector.css(".s-pagination-disabled") or selector.css(".s-pagination-selected")
        results_selector = selector.css(".puis-card-border")

        return {
            "query": query,
            "results": parse_results(results_selector),
            "current_page": parse_current_page(current_page_selector),
        }
