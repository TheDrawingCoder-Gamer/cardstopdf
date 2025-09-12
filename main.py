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
import itertools
import numpy as np
from proxygen.decklists import CustomCard, Card, parse_any
from proxygen.decklists.archidekt import parse_decklist as download_archidekt
from proxygen.decklists.moxfield import parse_decklist as download_moxfield

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

parser = argparse.ArgumentParser(prog="Cards To PDF")
parser.add_argument("--output", help="Output PDF", required=True)
parser.add_argument("--page-size", help="Page size (may be a descriptor or NxNunit. unit may be in/cm/mm/pt)")
parser.add_argument("--card-size", help="Card size")
parser.add_argument("--card-spacing", help="Card spacing. May be Nunit. Unit may be in/cm/mm/pt")
parser.add_argument("--bleed-edge", help="Use bleed edge. Set to Nunit. Unit may be in/cm/mm/pt")

subparsers = parser.add_subparsers(dest="subparser")

stitch_parser = subparsers.add_parser("stitch", help="Stitch Mode (from images, no duplicates)")
stitch_parser.add_argument(dest="input", help="Input Directory")

deck_parser = subparsers.add_parser("deck", help="Deck Mode (from file or URL, download and cache from scryfall)")
deck_parser.add_argument(dest="deck", help="Deck file or archidekt URL")
deck_parser.add_argument("--include-basic-lands", dest="basic_lands", action="store_true", help="By default, basic lands are excluded. Use this to include them.")
deck_parser.add_argument("--pair-dfc", dest="pair_dfc", action="store_true", help="Moves DFCs so that they are side by side and can be folded together.")
deck_parser.add_argument("--double-sided-mode", dest="double_sided", action="store_true", help="Make actual DFCs with double sided pages.")
deck_parser.add_argument("--back-output", dest="back_output", help="Split double sided face backs to a second PDF so that you can print double sided on a single sided printer.")

args = parser.parse_args()

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

if args.bleed_edge:
    bleed_edge = parse_length(args.bleed_edge)
else:
    bleed_edge = 0





failed = []


mode = "normal"
images = []


if args.subparser == "stitch":
    images = [[file] for file in os.listdir(args.input)]
elif args.subparser == "deck":
    if args.deck.startswith("https://"):
        if args.deck.startswith("https://archidekt.com/decks/"):
            archidekt_id = args.deck[8:].split("/")[2]
            # heh.......
            print("Downloading archidekt deck, this may take a while...")
            decklist = download_archidekt(archidekt_id)
        elif args.deck.startswith("https://moxfield.com/decks/"):
            moxfield_id = args.deck.split("/")[-1]
            print("Downloading moxfield deck, this may take a while...")
            decklist = download_moxfield(moxfield_id)
    else:
        decklist = parse_any(args.deck)

    for card in tqdm(decklist.cards, desc="Fetching card images"):
        if isinstance(card, CustomCard):
            da_uris = []
            failed_front = False
            failed_back = False
            if os.path.exists(card.front_face):
                da_uris.append(card.front_face)
            else:
                failed_front = True
            if card.back_face:
                if os.path.exists(card.back_face):
                    da_uris.append(card.back_face)
                else:
                    failed_back = True
            
            if failed_front or failed_back:
                err_fmt = ""
                if failed_front and failed_back:
                    err_fmt = "{name}: failed to locate front and back face"
                elif failed_front:
                    err_fmt = "{name}: failed to locate front face"
                else:
                    err_fmt = "{name}: failed to locate back face"
                
                failed.append(err_fmt.format(name=card.name))

                if failed_front:
                    failed.append("    front should be at {front}".format(front=card.front_face))
                if failed_back:
                    failed.append("    back should be at {back}".format(back=card.back_face))

                
            if len(da_uris) == 0:
                continue
        else:
            if not args.basic_lands and "Basic Land" in card["type_line"]:
                continue
            da_uris = [scryfall.get_image(uris["png"]) for uris in card.image_uris]
        images.append(da_uris) 

    mode = "normal"
    if args.back_output:
        mode = "split_sides"
    elif args.double_sided:
        mode = "double_sided"
    elif args.pair_dfc:
        mode = "paired"
else:
    print("No mode specified")
    parser.print_usage()
    exit(1)

if failed:
    print("Some downloads failed, so the PDF will be incomplete.")
    for f in failed:
        print(f)
    print("Do you want to try generating the PDF anyway? (y/n)")
    while True:
        response = input()
        if response == "y":
            print("Continuing...")
            break
        elif response == "n":
            print("Exiting...")
            exit(0)
        else:
            print("Please respond with y/n.")



print_cards(images, args.output, dfc_mode=mode, papersize=page_size, cardsize=card_size, card_spacing=card_spacing, bleed=bleed_edge, back_output=args.back_output)
