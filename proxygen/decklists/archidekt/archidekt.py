import requests

from proxygen.decklists import Decklist
import scryfall


def parse_decklist(archidekt_id: str) -> Decklist:
    decklist = Decklist()


    r = requests.get(f"https://archidekt.com/api/decks/{archidekt_id}/", headers=scryfall.headers)

    if r.status_code != 200:
        raise ValueError(f"Archidekt returned status code {r.status_code}")
    
    data = r.json()

    in_deck = {cat["name"] for cat in data["categories"] if cat["includedInDeck"]}

    for item in data["cards"]:
        count = item["quantity"]
        card_name = item["card"]["oracleCard"]["name"]
        set_id = item["card"]["edition"]["editioncode"]
        collector_number = item["card"]["collectorNumber"]

        if item["categories"] is not None and len(item["categories"]) > 0 and item["categories"][0] not in in_deck:
            continue

        card = scryfall.get_card(card_name=None, set_id=set_id, collector_number=collector_number)

        decklist.append_card(count, card)
    
    decklist.name = data["name"]

    return decklist
