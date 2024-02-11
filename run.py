from amazon_scraper import Amazon
import json

def main() -> None:
    amazon = Amazon()

    data = amazon.scrape_product("https://www.amazon.com.br/Ped%C3%B4metro-estudantes-multifuncional-despertador-eletr%C3%B4nico/dp/B0CBBZ69H5/ref=sr_1_1_sspa?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=2B28WKS7ZK04L&keywords=eletronicos&qid=1707656480&sprefix=eletronicos%2Caps%2C251&sr=8-1-spons&ufe=app_do%3Aamzn1.fos.6d798eae-cadf-45de-946a-f477d47705b9&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1")

    with open("data.json", "w") as file:
        json.dump(data, file)

if __name__ == "__main__":
    main()