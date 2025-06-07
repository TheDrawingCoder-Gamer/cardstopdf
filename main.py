import math
import itertools
import os
import argparse
import csv
import requests
import collections
import time
import json
import scryfall
from tqdm import tqdm
from proxygen.print_cards import print_cards, page_sizes, units, inch
import more_itertools
import numpy as np



parser = argparse.ArgumentParser(prog="Cards To PDF")
parser.add_argument("--output", help="Output PDF", required=True)
parser.add_argument("--page-size", help="Page size (may be a descriptor or NxNunit. unit may be in/cm/mm/pt)")
parser.add_argument("--card-size", help="Card size")
parser.add_argument("--card-spacing", help="Card spacing. May be Nunit. Unit may be in/cm/mm/pt")

subparsers = parser.add_subparsers(dest="subparser")

stitch_parser = subparsers.add_parser("stitch", help="Stitch Mode (from images, no duplicates)")
stitch_parser.add_argument(dest="input", help="Input Directory")

deck_parser = subparsers.add_parser("deck", help="Deck Mode (from csv, download and cache from scryfall)")
deck_parser.add_argument(dest="deck", help="Deck CSV (quantity, name, set code, collector number)")
deck_parser.add_argument("--include-basic-lands", dest="basic_lands", action="store_true", help="By default, basic lands are excluded. Use this to include them.")
deck_parser.add_argument("--pair-dfc", dest="pair_dfc", action="store_true", help="Moves DFCs so that they are side by side and can be folded together.")
deck_parser.add_argument("--double-sided-mode", dest="double_sided", action="store_true", help="Make actual DFCs with double sided pages.")

args = parser.parse_args()




def parse_size(size):
    x, remainder = more_itertools.before_and_after(lambda x : x != 'x', iter(size))
    x = float(''.join(x))
   
    next(remainder)
    y, remainder = more_itertools.before_and_after(lambda x : x.isnumeric() or x == '.', remainder)
    y = float(''.join(y))

    unit = ''.join(remainder)

    if not unit:
        unit = 'in'
    
    if unit not in units:
        raise ValueError(f"Invalid unit {unit}")

    unit_scale = units[unit]

    return np.array([x, y]) * unit_scale

def parse_length(size):
    x, unit = more_itertools.before_and_after(lambda x : x.isnumeric() or x == '.', iter(size))
    x = float(''.join(x))

    unit = ''.join(unit)

    if not unit:
        unit = 'in'

    if unit not in units:
        raise ValueError(f"Invalid unit {unit}")

    return x * units[unit]

failed = []


mode = "normal"
images = []

if args.subparser == "stitch":
    images = [[file] for file in os.listdir(args.input)]
elif args.subparser == "deck":
    with open(args.deck, "r") as deck:
        deck_csv = csv.reader(deck)
        rows = [row for row in deck_csv]
        for row in tqdm(rows, desc="Fetching card images"):
            da_uris = None
            if len(row) > 4:
                da_uris = [row[4]]
                if len(row) > 5:
                    da_uris.append(row[5])
                if len(row) > 6:
                    print(f"More than 2 images specified for card {row[1]} ... ignoring")
            else:
                # Ignore name as it may be mispelled
                da_card = scryfall.get_card(card_name=None, set_id=row[2], collector_number=row[3])
                if da_card:
                    if not args.basic_lands and "Basic Land" in da_card["type_line"]:
                        continue
                    da_faces = scryfall.get_faces(da_card)
                    da_uris = [scryfall.get_image(face["image_uris"]["png"]) for face in da_faces]
            if da_uris:
                for x in range(int(row[0])):
                    # append for DFC
                    images.append(da_uris)
    


    mode = "normal"
    if args.double_sided:
        mode = "double_sided"
    elif args.pair_dfc:
        mode = "paired"
else:
    print("No mode specified")
    parser.print_usage()
    exit(1)


if args.page_size:
    if args.page_size.lower() in page_sizes:
        page_size = np.array(page_sizes[args.page_size.lower()])
    else:
        page_size = parse_size(args.page_size)
else:
    page_size = np.array(page_sizes["letter"])

if args.card_size:
    card_size = parse_size(args.card_size)
else:
    card_size = np.array([2.5 * inch, 3.5 * inch])

if args.card_spacing:
    card_spacing = parse_length(args.card_spacing)
else:
    card_spacing = 0.1 * inch

print_cards(images, args.output, dfc_mode=mode, papersize=page_size, cardsize=card_size, card_spacing=card_spacing)
        
if failed:
    print("Some downloads failed, so the PDF is incomplete.")
    for f in failed:
        print(f)

    

    



