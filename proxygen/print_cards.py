import fpdf
from fpdf import FPDF
import numpy as np
import itertools
import collections
from pathlib import Path
from tqdm import tqdm

image_size = np.array([745, 1040])

def _occupied_space(cardsize, pos, card_spacing: float, closed: bool = False):
    return cardsize * (pos * image_size + np.clip(2 * pos, 0, None) * card_spacing) / image_size

page_sizes = {
        "a3": (841.89, 1190.55),
        "a4": (595.28, 841.89),
        "a5": (420.94, 595.28),
        "letter": (612, 792),
        "legal": (612, 1008)
        }

inch = 72
cm = inch / 2.54
mm = cm * 0.1

units = {
        "pt": 1,
        "in": inch,
        "cm": cm,
        "mm": mm
        }

def print_cards(
            images: list[list[str | Path]],
            filepath: str | Path,
            papersize = np.array([612, 792]),
            cardsize= np.array([2.5 * inch, 3.5 * inch]),
            card_spacing = 0.1 * inch,
            dfc_mode: str = "normal" # normal, paired, double_sided
            ) -> None:


    N = np.floor(papersize / (cardsize + card_spacing)).astype(int)
    if N[0] == 0 or N[1] == 0:
        raise ValueError(f"Paper size too small: {papersize}")

    cards_per_sheet = np.prod(N)
    offset = (papersize - _occupied_space(cardsize, N, card_spacing, closed=True)) / 2


    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    is_double_sided = False
    output_images = []



    if dfc_mode == "double_sided":
        single_sided = []
        dfcs = collections.deque()
        non_dfcs = collections.deque()
        for card in images:
            if len(card) == 1:
                non_dfcs.append(card)
            else:
                assert(len(card) == 2)
                dfcs.append(card)
        frky_images = []
        frky_images.extend(dfcs)
        frky_images.extend(non_dfcs)

        for group in itertools.batched(frky_images, cards_per_sheet):
            back_faces = [None] * cards_per_sheet
            front_faces = [None] * cards_per_sheet
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
    elif dfc_mode == "paired":
        dfcs = collections.deque()
        non_dfcs = collections.deque()
        for card in images:
            if len(card) == 1:
                non_dfcs.append(card[0])
            else:
                assert(len(card) == 2)
                dfcs.append(card)
        while dfcs:
            dfc = dfcs.popleft()
            output_images.extend(dfc)
            if non_dfcs:
                output_images.append(non_dfcs.popleft())
            else:
                output_images.append(None)
        output_images.extend(non_dfcs)
    else:
        output_images = list(itertools.chain.from_iterable(images))

    
            
    pdf = FPDF(orientation="P", unit="pt", format=papersize)

    for i, image in enumerate(tqdm(output_images, desc="Plotting cards")):
        if i % cards_per_sheet == 0:
            pdf.add_page()
        
        if image:
            x = (i % cards_per_sheet) % N[0]
            y = (i % cards_per_sheet) // N[0]
   
            if is_double_sided and (i % (cards_per_sheet * 2)) >= cards_per_sheet:
                x = N[0] - (x + 1)
        
            lower = offset + _occupied_space(cardsize, np.array([x, y]), card_spacing)

            pdf.image(str(image), x=lower[0], y=lower[1], w=cardsize[0], h=cardsize[1])


    
    tqdm.write(f"Writing to {filepath}")
    pdf.output(filepath)
