from reportlab.lib.pagesizes import portrait, letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame
from reportlab.lib.utils import Image as PilImage
import math
import itertools
import os

# assume ratio is proper or else IT ALL BURNS!!!!
card_width = 2.5 * inch
card_height = 3.5 * inch

card_spacing = 0.05 * inch

horz_bleed_edge = 0.3 * inch

vert_bleed_edge = 0.15 * inch

# TODO: ask for flag
source_dir = "input"

def draw_image_batch(canvas, images):
    
    for idx, image in enumerate(images):
        y = vert_bleed_edge + math.floor(idx / 3) * (card_height + card_spacing)
        x = horz_bleed_edge + (idx % 3) * (card_width + card_spacing)

        canvas.drawImage(os.path.join(source_dir, image), x, y, card_width, card_height)



pdf_file = "deck.pdf"

canvas = canvas.Canvas(pdf_file, pagesize=portrait(letter))

#test_files = os.listdir(source_dir)[:9]

#draw_image_batch(canvas, test_files)
#canvas.showPage()

for files in itertools.batched(os.listdir(source_dir), 9):
    draw_image_batch(canvas, files)
    canvas.showPage()

canvas.save()

    



