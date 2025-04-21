from reportlab.lib.pagesizes import portrait, letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame
from reportlab.lib.utils import Image as PilImage
import math
import itertools
import os
import argparse
import csv
import requests
from pathvalidate import sanitize_filename
from io import BytesIO
import time

headers = {"user-agent": "TheDrawingCoder-Gamer/cardstopdf/0.0.2", "accept": "*/*" }


parser = argparse.ArgumentParser(prog="Cards To PDF")
parser.add_argument("--output", help="Output PDF", required=True)

subparsers = parser.add_subparsers(dest="subparser")

stitch_parser = subparsers.add_parser("stitch", help="Stitch Mode (from images, no duplicates)")
stitch_parser.add_argument("--input", help="Input Directory", required=True)

deck_parser = subparsers.add_parser("deck", help="Deck Mode (from csv, download and cache from scryfall)")
deck_parser.add_argument("--deck", "--input", help="Deck CSV (quantity, name, set code, collector number)", required=True)
#deck_parser.add_argument("--cache", dest="cache", default="cache", help="Override cache dir (default 'cache')")
#deck_parser.add_argument("--nocache", dest="cache", action="store_const", const=None, help="Disable caching")
deck_parser.add_argument("--include-basic-lands", dest="basic_lands", action="store_true", help="By default, basic lands are excluded. Use this to include them.")


args = parser.parse_args()

# assume ratio is proper or else IT ALL BURNS!!!!
card_width = 2.5 * inch
card_height = 3.5 * inch

card_spacing = 0.05 * inch

horz_bleed_edge = 0.3 * inch

vert_bleed_edge = 0.15 * inch


canvas = canvas.Canvas(args.output, pagesize=portrait(letter))

def filename_of_card(name, set_code, collector_num):
    return sanitize_filename(f"{name} ({set_code} {collector_num})")

failed = []
def uris_of_data(data):
    layout = data["layout"]
    if layout == "transform" or layout == "modal_dfc":
        return [(f"{filename_of_card(data["name"], data["set"], data["collector_number"])} - face {sanitize_filename(card_face["name"])}", card_face["image_uris"]["png"]) for card_face in data["card_faces"]] 
    elif layout == "meld":
        failed.append(data["name"] + " - Back face (can't fetch meld backface due to api)")

        return [(filename_of_card(data["name"], data["set"], data["collector_number"]), data["image_uris"]["png"])]
    elif data["image_uris"] and data["image_uris"]["png"]:
        return [(filename_of_card(data["name"], data["set"], data["collector_number"]), data["image_uris"]["png"])]
    else:
        failed.append(data["name"] + " - no image found. This tool probably doesn't support this kind of card.")
        return []

def uris(name, set_code, collector_num, basic_lands=False):
    da_url = f"https://api.scryfall.com/cards/{set_code}/{collector_num}"
    r = requests.get(da_url, headers=headers)

    # do this or else i get banned : (
    time.sleep(0.1)
    
    data = r.json()

    if (not basic_lands) and "Basic Land" in data["type_line"]:
        # empty so i dont crash : (
        return []
        
    return uris_of_data(data)


if args.subparser == "stitch":
    source_dir = args.input

    def draw_image_batch(canvas, images):
        
        for idx, image in enumerate(images):
            y = vert_bleed_edge + math.floor(idx / 3) * (card_height + card_spacing)
            x = horz_bleed_edge + (idx % 3) * (card_width + card_spacing)

            canvas.drawImage(os.path.join(source_dir, image), x, y, card_width, card_height)

    for files in itertools.batched(os.listdir(source_dir), 9):
        draw_image_batch(canvas, files)
        canvas.showPage()
elif args.subparser == "deck":
    image_uris = []
    with open(args.deck, "r") as deck:
        deck_csv = csv.reader(deck)
        for row in deck_csv:
            da_uris = True
            if len(row) > 4:
                da_uris = [(filename_of_card(row[1], row[2], row[3]), {"local_file": row[4] })]
            else:
                da_uris = uris(row[1], row[2], row[3], basic_lands=args.basic_lands)
            for x in range(int(row[0])):
                image_uris.extend(da_uris)

    def draw_image_batch(canvas, images):
        
        for idx, (_, image) in enumerate(images):
            y = vert_bleed_edge + math.floor(idx / 3) * (card_height + card_spacing)
            x = horz_bleed_edge + (idx % 3) * (card_width + card_spacing)
           
            # I LOVE FREAK TYPING
            if "local_file" in image:
               
                canvas.drawInlineImage(image["local_file"], x, y, card_width, card_height)
            else:
                r = requests.get(image)

                canvas.drawInlineImage(PilImage.open(BytesIO(r.content)), x, y, card_width, card_height)

    for batch in itertools.batched(image_uris, 9):
        draw_image_batch(canvas, batch)
        canvas.showPage()
    
        
        

    

canvas.save()

    



