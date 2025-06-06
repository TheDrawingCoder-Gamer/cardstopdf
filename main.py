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
import collections
from pathvalidate import sanitize_filename
from io import BytesIO
import time
import json

headers = {"user-agent": "TheDrawingCoder-Gamer/cardstopdf/0.0.2", "accept": "*/*" }


parser = argparse.ArgumentParser(prog="Cards To PDF")
parser.add_argument("--output", help="Output PDF", required=True)

subparsers = parser.add_subparsers(dest="subparser")

stitch_parser = subparsers.add_parser("stitch", help="Stitch Mode (from images, no duplicates)")
stitch_parser.add_argument(dest="input", help="Input Directory")

deck_parser = subparsers.add_parser("deck", help="Deck Mode (from csv, download and cache from scryfall)")
deck_parser.add_argument(dest="deck", help="Deck CSV (quantity, name, set code, collector number)")
deck_parser.add_argument("--cache", dest="cache", default="cache", help="Override cache dir (default 'cache')")
deck_parser.add_argument("--nocache", dest="cache", action="store_const", const=None, help="Disable caching")
deck_parser.add_argument("--include-basic-lands", dest="basic_lands", action="store_true", help="By default, basic lands are excluded. Use this to include them.")
deck_parser.add_argument("--pair-dfc", dest="pair_dfc", action="store_true", help="Moves DFCs so that they are side by side and can be folded together.")
deck_parser.add_argument("--double-sided-mode", dest="double_sided", action="store_true", help="Make actual DFCs with double sided pages.")


args = parser.parse_args()

if args.cache and (not os.path.exists(args.cache)):
    os.mkdir(args.cache)

# assume ratio is proper or else IT ALL BURNS!!!!
card_width = 2.5 * inch
card_height = 3.5 * inch

card_spacing = 0.05 * inch

horz_bleed_edge = 0.3 * inch

vert_bleed_edge = 0.15 * inch

page_width, page_height = letter

canvas = canvas.Canvas(args.output, pagesize=portrait(letter))

def cache_check(set_code, collector_num, basic_lands=False):
    if not args.cache:
        return None

    # should be all valid characters here
    cache_file = os.path.join(args.cache, f"{set_code} {collector_num}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as txt:
            data = json.load(txt)
            if "basic_land" in data and data["basic_land"] and not basic_lands:
                return []
            else:
                return [{ "local_file": os.path.join(args.cache, file)} for file in data["images"]]



    return None

def save_cache(set_code, collector_num, basic_lands=False):
    infos = freaky_uris(set_code, collector_num)

    images = []
    for idx, uri in enumerate(infos["images"]):
        r = requests.get(uri, headers=headers)
        
        image_file = f"{set_code} {collector_num} {idx}.png"
        with open(os.path.join(args.cache, image_file), "wb") as bin:
            bin.write(r.content)

        images.append(image_file)

    with open(os.path.join(args.cache, f"{set_code} {collector_num}.json"), "w") as txt:
        json.dump({"basic_land": infos["basic_land"], "images": images}, txt)

    if infos["basic_land"] and not basic_lands:
        return []
    else:
        return [{"local_file": os.path.join(args.cache, image)} for image in images]

def filename_of_card(name, set_code, collector_num):
    return sanitize_filename(f"{name} ({set_code} {collector_num})")

failed = []
def uris_of_data(data):
    layout = data["layout"]
    if layout == "transform" or layout == "modal_dfc":
        return [card_face["image_uris"]["png"] for card_face in data["card_faces"]]
    elif layout == "meld":
        failed.append(data["name"] + " - Back face (can't fetch meld backface due to api)")

        return [data["image_uris"]["png"]]
    elif data["image_uris"] and data["image_uris"]["png"]:
        return [data["image_uris"]["png"]]
    else:
        failed.append(data["name"] + " - no image found. This tool probably doesn't support this kind of card.")
        return []

def freaky_uris(set_code, collector_num):
    da_url = f"https://api.scryfall.com/cards/{set_code}/{collector_num}"
    r = requests.get(da_url, headers=headers)

    time.sleep(0.1)

    data = r.json()

    return { "basic_land": ("Basic Land" in data["type_line"]), "images": uris_of_data(data) }

def uris(name, set_code, collector_num, basic_lands=False):
    da_url = f"https://api.scryfall.com/cards/{set_code}/{collector_num}"
    r = requests.get(da_url, headers=headers)

    # do this or else i get banned : (
    time.sleep(0.1)
    
    data = r.json()

    # TODO: this breaks with cache
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
                da_uris = [{"local_file": row[4] }]
                if len(row) > 5:
                    da_uris.append({"local_file": row[5]})
                if len(row) > 6:
                    print(f"More than 2 images specified for card {row[1]} ... ignoring")
            else:
                if args.cache:
                    cache_res = cache_check(row[2], row[3], basic_lands=args.basic_lands)
                    if cache_res:
                        da_uris = cache_res
                    else:
                        da_uris = save_cache(row[2], row[3], basic_lands=args.basic_lands)
                else:
                    da_uris = uris(row[1], row[2], row[3], basic_lands=args.basic_lands)
            for x in range(int(row[0])):
                # append for DFC
                image_uris.append(da_uris)
    


    def draw_image_batch(canvas, images):
        
        for idx, image in enumerate(images):
            # if we have extra slots, place them on the back (it's the back side)
            if idx == 9:
                canvas.showPage()
            if image:
                y = vert_bleed_edge + math.floor((idx % 9) / 3) * (card_height + card_spacing)
                x = horz_bleed_edge + (idx % 3) * (card_width + card_spacing)
                if idx >= 9:
                    x = page_width - horz_bleed_edge - ((idx % 3) + 1) * (card_width + card_spacing)
               
                # I LOVE FREAK TYPING
                if "local_file" in image:
                   
                    canvas.drawInlineImage(image["local_file"], x, y, card_width, card_height)
                else:
                    r = requests.get(image)

                    canvas.drawInlineImage(PilImage.open(BytesIO(r.content)), x, y, card_width, card_height)
        canvas.showPage()
    
    output_images = []

    is_double_sided = False

    if args.double_sided:
        single_sided = []
        for group in itertools.batched(image_uris, 9):
            back_faces = [None] * 9
            front_faces = [None] * 9
            for idx, card in enumerate(group):
                front_faces[idx] = card[0]
                if len(card) == 2:
                    is_double_sided = True
                    back_faces[idx] = card[1]

            if not is_double_sided:
                single_sided.extend(front_faces)

            output_images.extend(front_faces)
            output_images.extend(back_faces)

        if not is_double_sided:
            output_images = single_sided

    elif args.pair_dfc:
        mdfcs = collections.deque()
        non_mdfcs = collections.deque()
        for card in image_uris:
            if len(card) == 1:
                non_mdfcs.append(card[0])
            else:
                # should NOT be any cards with more than 2 faces.
                # if there is god is dead
                assert(len(card) == 2)
                mdfcs.append(card)
        while mdfcs:
            mdfc = mdfcs.popleft()
            output_images.extend(mdfc)
            if non_mdfcs:
                output_images.append(non_mdfcs.popleft())
            else:
                output_images.append(None)
        output_images.extend(non_mdfcs)
    else:
        output_images = list(itertools.chain.from_iterable(image_uris))


    batch_size = 9
    if is_double_sided:
        batch_size = 18

    for batch in itertools.batched(output_images, batch_size):
        draw_image_batch(canvas, batch)
    
        
        
if failed:
    print("Some downloads failed, so the PDF is incomplete.")
    for f in failed:
        print(f)

    

canvas.save()

    



