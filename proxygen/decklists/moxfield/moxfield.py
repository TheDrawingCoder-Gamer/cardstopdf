from collections.abc import Sequence

import requests
import scryfall
from proxygen.decklists import Decklist

def parse_decklist(moxfield_id: str, zones: Sequence[str] = ("commander", "mainboard")):
    decklist = Decklist()

    r = requests.get(f"https://api2.moxfield.com/v3/decks/all/{moxfield_id}", headers=scryfall.headers)

    if r.status_code != 200:
        raise ValueError(f"Moxfield returned status code {r.status_code}")

    data = r.json()

    for name, board in data["boards"].items():
        if name not in zones:
            continue
        for card in board["cards"].values():
            count = card["quantity"]
            scryfall_id = card["card"]["scryfall_id"]
            decklist.append_card(count, scryfall.card_by_id()[scryfall_id])

    decklist.name = data["name"]

    return decklist

