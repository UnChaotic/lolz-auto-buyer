import logging
import urllib.parse

from src.config import Config
from src.market import MarketAPI, MarketBuyError, MarketItem
from src.market.api import parse_search_data
from src.telegram import TelegramAPI

TELEGRAM_MESSAGE = (
    '🎊 Account purchased: <a href="https://lzt.market/{item_id}">'
    "{title}</a>\n"
    "💲 Price: <code>{price}₽</code>\n"
    '👷 Seller: <a href="https://zelenka.guru/members/{seller_id}">'
    "{seller_username}</a>"
)


def main():
    config = Config.load_config("config.ini")
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
    )
    lolzteam_token = config.lolzteam.token

    telegram = TelegramAPI(config.telegram.bot_token)
    market = MarketAPI(lolzteam_token)
    count_purchase = 0
    searches = []
    for search_url in config.lolzteam.search_urls_list:
        category, params = parse_search_data(search_url)
        searches.append((category, params))

    while True:
        for search, params in searches:
            search_result = market.search(search, params)
            items = search_result.get("items", [])

            logging.info(
                "Found %s accounts for search %s with parameters %s",
                len(items),
                search,
                urllib.parse.unquote(params),
            )

            for item in items:
                item_id = item["item_id"]
                market_item = MarketItem(item, lolzteam_token)
                try:
                    logging.info("Buying account %s", item_id)
                    market_item.fast_buy()
                except MarketBuyError as error:
                    logging.warning(
                        "Error occurred while trying to buy account %s: %s",
                        item_id,
                        error.message,
                    )
                    continue
                else:
                    logging.info("Account %s successfully purchased!", item_id)
                    count_purchase += 1

                    account_object = market_item.item_object
                    seller = account_object["seller"]
                    telegram.send_message(
                        TELEGRAM_MESSAGE.format(
                            item_id=item_id,
                            title=account_object["title"],
                            price=account_object["price"],
                            seller_id=seller["user_id"],
                            seller_username=seller["username"],
                        ),
                        config.telegram.id,
                        parse_mode="HTML",
                    )

                    if count_purchase >= config.lolzteam.count:
                        logging.info(
                            "Successfully purchased %s accounts, work completed.",
                            count_purchase,
                        )
                        exit()
                    break


if __name__ == "__main__":
    main()
