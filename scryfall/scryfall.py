from __future__ import annotations

from scryfall.rate_limit import RateLimiter
from pathlib import Path
from tempfile import gettempdir
import threading
import pickle
import json
from functools import cache as memoize

import requests



headers = {"user-agent": "TheDrawingCoder-Gamer/cardstopdf/0.0.2", "accept": "*/*" }
cache = Path(gettempdir()) / "bublis_scryfall_cache"
cache.mkdir(parents=True, exist_ok=True)
scryfall_rate_limiter = RateLimiter(delay=0.1)
_download_lock = threading.Lock()

def get_image(image_uri):
    split = image_uri.split("/")
    file_name = split[-5] + "_" + split[-4] + "_" + split[-1].split("?")[0]
    return get_file(file_name, image_uri)

def get_file(file_name, url):
    file_path = cache / file_name
    with _download_lock:
        if not file_path.is_file():
            if "api.scryfall.com" in url:
                with scryfall_rate_limiter:
                    download(url, file_path)
            else:
                download(url, file_path)

    return str(file_path)

def download(url, dst, chunk_size = 1024 * 4):
    with requests.get(url, stream=True, headers=headers) as req:
        req.raise_for_status()
        with open(dst, "xb") as f:
            for chunk in req.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

def depaginate(url):
    with scryfall_rate_limiter:
        response = requests.get(url, headers=headers).json()
    assert response["object"]
    if "data" not in response:
        return []
    data = response["data"]
    if response["has_more"]:
        data = data + depaginate(response["next_page"])

    return data

@memoize
def _get_database(database_name="default_cards"):
    databases = depaginate("https://api.scryfall.com/bulk-data")
    bulk_data = [database for database in databases if database["type"] == database_name]
    if len(bulk_data) != 1:
        raise ValueError(f"Unknown database {database_name}")

    bulk_file = Path(get_file(bulk_data[0]["download_uri"].split("/")[-1], bulk_data[0]["download_uri"]))
    pickle_file = bulk_file.with_suffix(".pickle")
    if not pickle_file.is_file():
        with open(bulk_file, encoding="utf-8") as json_file:
            data = json.load(json_file)
        with open(pickle_file, "wb") as pickle_file:
            pickle.dump(data, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)
        return data
    else:
        with open(pickle_file, "rb") as f:
            return pickle.load(f)

def canonic_card_name(name):
    name = name.lower()

    # didn't copy paste æ btw
    name = name.replace("æ", "ae")

    return name

def get_cards(database="default_cards", **kwargs):
    cards = _get_database(database)

    for key, value in kwargs.items():
        if value is not None:
            value = value.lower()

            if key == "name":
                value = canonic_card_name(value)

            cards = [card for card in cards if key in card and card[key].lower() == value]

    return cards

def get_card(card_name: str, set_id: str = None, collector_number = None):
    cards = get_cards(name=card_name, set=set_id, collector_number=collector_number)
    
    return cards[0] if len(cards) > 0 else None

def get_faces(card):
    if "image_uris" in card:
        return [card]
    elif "card_faces" in card and "image_uris" in card["card_faces"][0]:
        return card["card_faces"]
    else:
        raise ValueError(f"Unknown layout {card['layout']}")
