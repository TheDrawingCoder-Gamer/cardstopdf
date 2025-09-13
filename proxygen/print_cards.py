import fpdf
from fpdf import FPDF
import numpy as np
import itertools
import collections
from pathlib import Path
from tqdm import tqdm
from PIL import Image, ImageDraw
import os
import tempfile

# sus...

image_width = 745

# changes after every print_pdf call
image_size = np.array([745, 1040])

def _occupied_space(container_size, pos, closed: bool = False):
    return container_size * pos

page_sizes = {
        "a3": (841.89, 1190.55),
        "a4": (595.28, 841.89),
        "a5": (420.94, 595.28),
        "letter": (612, 792),
        "legal": (612, 1008)
        }


dpi = 300
inch = 72
cm = inch / 2.54
mm = cm * 0.1
# i did the thing i learned in science class, ts should NOT crash
px = inch / dpi

units = {
        "pt": 1,
        "in": inch,
        "cm": cm,
        "mm": mm
        }

line_width = 0.3 * mm

def pt_to_px(i):
    return np.rint((i / inch) * dpi).astype(int)

class PDFDrawable:
    def __init__(self, pagesize, output):
        self.pdf = FPDF('P', 'pt', format=pagesize)
        self.pdf.set_line_width(line_width)
        self.output = output

    def line(self, x1, y1, x2, y2, color):
        self.pdf.set_draw_color(r=color[0], g=color[1],b=color[2])
        self.pdf.line(x1, y1, x2, y2)
    
    def filled_rect(self, x, y, w, h, color):
        self.pdf.set_fill_color(r=color[0],g=color[1],b=color[2])
        self.pdf.rect(x, y, w, h, style='F')
    
    def image(self, path, x, y, w, h):
        self.pdf.image(path, x, y, w, h)

    def inmem_image(self, im, x, y, w, h):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            tmp = f.name
        
        im.save(tmp)
        # loaded into memory
        # this is probably really bad if you have 10 mountains
        self.pdf.image(tmp, x, y, w, h)
        os.unlink(tmp)

    def add_page(self):
        self.pdf.add_page()


    
    def write_to_output(self):
        print("Writing to {out}".format(out=self.output))
        self.pdf.output(self.output)

class PILDrawable:
    def __init__(self, pagesize, output):
        self.pagesize = pt_to_px(pagesize)
        self.img = None
        self.draw = None
        try: 
            str(output) % 1
        except TypeError:
            print("Output file must have number format (try something like file%03d)")
            exit(1)
        self.output = str(output)
        self.page = 0
    
    def line(self, x1, y1, x2, y2, color):
        self.draw.line([pt_to_px(x1), pt_to_px(y1), pt_to_px(x2), pt_to_px(y2)], fill=color, width=pt_to_px(line_width))
    
    def filled_rect(self, x, y, w, h, color):
        self.draw.rectangle([pt_to_px(x), pt_to_px(y), pt_to_px(x + w), pt_to_px(y + h)], fill=color)
    
    # for testing only, no need to mirror to PDF for now
    def rect(self, x, y, w, h, color):
        self.draw.rectangle([pt_to_px(x), pt_to_px(y), pt_to_px(x + w), pt_to_px(y + h)], outline=color, width=pt_to_px(line_width))
    
    def image(self, path, x, y, w, h):
        if os.path.exists(path):
            with Image.open(path) as im:
                self.inmem_image(im, x, y, w, h)
    def inmem_image(self, im, x, y, w, h):
        im_resized = im.resize((pt_to_px(w), pt_to_px(h)))
        self.img.paste(im_resized, box=(pt_to_px(x), pt_to_px(y)))
    
    def save(self):
        if self.img:
            save_to = self.output % self.page
            self.img.save(save_to)
            self.img.close()
    def add_page(self):
        if self.img:
            print("saving page {}".format(self.page))
        self.save()
        self.img = Image.new(mode="RGB", size=(self.pagesize[0],self.pagesize[1]), color=(255,255,255))
        self.draw = ImageDraw.Draw(self.img)
        self.page = self.page + 1


    def write_to_output(self):
        print("saving last page")
        self.save()


def get_drawable(pagesize, filepath):
    if str(filepath).endswith('pdf'):
        return PDFDrawable(pagesize, filepath)
    else:
        return PILDrawable(pagesize, filepath)


black = (0, 0, 0)
gray = (128, 128, 128)

def draw_guide(pdf, data):
    cardsize = data["cardsize"]
    bleed = data["bleed"]
    papersize = data["papersize"]
    N = data["N"]
    offset = data["offset"]
    card_spacing = data["card_spacing"]
    guide_mode = data["guide_mode"]
    container_size = data["container_size"]
    

    row_points = []
    col_points = []

    if bleed > 0:
        move_by = bleed
    else:
        move_by = card_spacing / 2
    for x in range(0, N[0] + 1):
        x2 = offset[0] + _occupied_space(container_size, x)[0]
        if guide_mode == "edge" and move_by != 0:
            if x == 0 or x != N[0]:
                col_points.append(x2 + move_by)
            if x == N[0] or x != 0:
                col_points.append(x2 - move_by)
        else:
            if x == 0:
                col_points.append(x2 + move_by)
            elif x == N[0]:
                col_points.append(x2 - move_by)
            else:
                col_points.append(x2)
    for y in range(0, N[1] + 1):
        y2 = offset[1] + _occupied_space(container_size, y)[1]

        if guide_mode == "edge" and move_by != 0:
            if y == 0 or y != N[1]:
                row_points.append(y2 + move_by)
            if y == N[1] or y != 0:
                row_points.append(y2 - move_by)
        else:
            if y == 0:
                row_points.append(y2 + move_by)
            elif y == N[1]:
                row_points.append(y2 - move_by)
            else:
                row_points.append(y2)
    cross_size = 0.5 * mm
    # offset to be flush with the edge of the cards
    flush_offset = offset + card_spacing / 2
    for r in row_points:
        for c in col_points:
            pdf.line(c - cross_size, r, c + cross_size, r, color=gray)
            pdf.line(c, r - cross_size, c, r + cross_size, color=gray)
    for col in col_points:
        pdf.line(x1=col, y1=0, x2=col, y2=flush_offset[1], color=black)
        pdf.line(col, papersize[1] - flush_offset[1], col, papersize[1], color=black)
    for row in row_points:
        pdf.line(0, row, flush_offset[0], row, color=black)
        pdf.line(papersize[0] - flush_offset[0], row, papersize[0], row, color=black)
        

def draw_pdf(filepath, desc, images, draw_mode, data):
    cardsize = data["cardsize"]
    bleed = data["bleed"]
    papersize = data["papersize"]
    N = data["N"]
    offset = data["offset"]
    card_spacing = data["card_spacing"]
    guide = data["guide"]
    container_size = data["container_size"]
    card_zoom = data["card_zoom"]
    
    cards_per_sheet = np.prod(N)

    pdf = get_drawable(papersize, filepath)

    if card_spacing > 0:
        center_by = (container_size - cardsize) / 2
    else:
        center_by = 0

    for i, image in enumerate(tqdm(images, desc=desc)):
        if i % cards_per_sheet == 0:
            
            if i != 0 and guide:
                draw_guide(pdf, data)
            pdf.add_page()

        if image:
            x = (i % cards_per_sheet) % N[0]
            y = (i % cards_per_sheet) // N[0]
   
            if draw_mode == "back" or (draw_mode == "double" and (i % (cards_per_sheet * 2)) >= cards_per_sheet):
                x = N[0] - (x + 1)
        
            full_lower = offset + _occupied_space(container_size, np.array([x, y]))
            lower = full_lower + center_by
            
            # pdf.filled_rect(x=lower[0], y=lower[1], w=cardsize[0], h=cardsize[1], color=black)
            if card_zoom > 0:
                with Image.open(image) as im:
                    im_resized = im.resize((pt_to_px(cardsize[0] + card_zoom), pt_to_px(cardsize[1] + card_zoom)))
                    zoom_px = pt_to_px(card_zoom)
                    crop_by = np.rint((np.array(im_resized.size) - pt_to_px(container_size)) / 2).astype(int)
                    cropped = im_resized.crop((crop_by[0], crop_by[1], im_resized.width - crop_by[0], im_resized.height - crop_by[1]))
                    pdf.inmem_image(cropped, lower[0], lower[1], container_size[0], container_size[1])
            else:
                pdf.image(str(image), x=lower[0], y=lower[1], w=cardsize[0], h=cardsize[1])
                # pdf.rect(full_lower[0], full_lower[1], container_size[0], container_size[1], black)
                
    if guide:
        draw_guide(pdf, data)
    
    # tqdm.write(f"Writing to {filepath}")
    pdf.write_to_output()

def print_cards(
            images: list[list[str | Path]],
            filepath: str | Path,
            papersize = np.array([612, 792]),
            cardsize= np.array([2.5 * inch, 3.5 * inch]),
            card_spacing = 0.1 * inch,
            dfc_mode: str = "normal", # normal, paired, double_sided, split_sides
            bleed: float = 0,
            back_output: str | Path | None = None,
            show_guide: bool = False,
            ) -> None:

    if bleed > 0:
        container_size = cardsize + bleed * 2 + 1 * px
        card_spacing = 0
        card_zoom = 6.2 * mm
    else:
        container_size = cardsize + card_spacing
        card_zoom = 0

    N = np.floor(papersize / container_size).astype(int)
    if N[0] == 0 or N[1] == 0:
        raise ValueError(f"Paper size too small: {papersize}")

    cards_per_sheet = np.prod(N)
    # preserve aspect ratio
    image_size = (cardsize / cardsize.sum()) * image_width
    offset = ((papersize - _occupied_space(container_size, N)) / 2)

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    is_double_sided = False
    output_images = []
    back_images = []

    shared_data = {
        "papersize": papersize,
        "offset": offset,
        "cardsize": cardsize,
        "bleed": bleed,
        "N": N,
        "card_spacing": card_spacing,
        "guide": show_guide,
        "container_size": container_size,
        "card_zoom": card_zoom,
        "guide_mode": "edge", # center, edge
    }

    if dfc_mode == "split_sides":
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

        has_done_all_dfc = False
        for group in itertools.batched(frky_images, cards_per_sheet):
            has_dfc = False
            back_faces = [None] * cards_per_sheet
            front_faces = [None] * cards_per_sheet
            for idx, card in enumerate(group):
                front_faces[idx] = card[0]
                if len(card) == 2:
                    assert(not has_done_all_dfc)
                    has_dfc = True
                    back_faces[idx] = card[1]
            
            if not has_dfc:
                has_done_all_dfc = True
            
            output_images.extend(front_faces)
            if not has_done_all_dfc:
                back_images.extend(back_faces)
    elif dfc_mode == "double_sided":
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

    if dfc_mode == "double_sided":
        draw_mode = "double"
    else:
        draw_mode = "normal"
    draw_pdf(filepath, "Plotting cards", output_images, draw_mode, shared_data)
    


    if len(back_images) > 0:
        draw_pdf(back_output, "Plotting back faces", back_images, "back", shared_data)
        

