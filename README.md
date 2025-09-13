# Cards to PDF

converts cards to pdf/image files

because of how bad of a format pdf is i found that a single page takes ~20s. This means a full commander deck with all unique cards would take
4 minutes to generate. Have fun with that!

you can also output PNGs - it takes ~3s per page (mostly taken saving the page) so a full commander deck with all unique cards would take half a minute.

## Support

This supports 

* Normal Cards
* Transform, MDFC cards

This does NOT support

* Meld cards

I've complained to scryfall about it but they haven't updated their api : (.

## Usage

There are two ways to use this: via a CSV document with your deck, or with a bunch of image files.

### Shared Options

You can specify page size, card size, and spacing between cards:

```
python main.py --page-size letter --card-size 3.5x5in --card-spacing 0.1in
```

Page size can be named (a4, a3, a5, letter, legal) or specified like how card size is specified above.

The unit at the end of sizes and lengths may be mm, cm, in, or pt. If it's omitted, it's assumed to be inches.

Instead of card spacing, you can select the bleed edge size. This will cut into the image, so for card art not specifically designed for
bleed edge (any card art uploaded to MPC Autofill has bleed edge) will come out smaller than it's supposed to.

```
python main.py --bleed-edge 1mm
```

Specifying bleed edge will disable card spacing.

You can also draw guide lines with `--guide`:

```
python main.py --guide
```

Specifying the PDF output is just passing an output with the PDF extension:
```
python main.py --output out.pdf
```

Image formats are more complicated; you'll need to provide a valid format string for numbers.
This uses python's old style formatting (so it's similar to C and ffmpeg's options), seen [here](https://docs.python.org/3/library/stdtypes.html#old-string-formatting).

The most basic case is a padded number:
```
python main.py --output page%03d.png
```

This will output page001.png, page002.png ... page999.png

The `--back-output` option will be formatted the same way.

### Stitch mode

Pass in all files you want to stitch together to stitch mode:
```
python main.py --output out.pdf stitch file1.png file2.png file3.png
```

All inputs will be put on the page. It's assumed the images are in the correct aspect ratio, and stretching/clipping
may occur if it's not in the correct aspect ratio.

### Deck mode


You can pass in decklist, like so:

```
python main.py --output out.pdf deck deck.txt
```


There are multiple valid formats for the decklist.

Exporting from Archidekt as Arena is the easiest format and doesn't require any editing.

You can also export an CSV. You have to check "Edition Code" and "Collector Number" in that order on Archidekt.

You can add custom cards as well. In the Arena format, this line will add a custom card:

```
cstm: 1 Card Name [front_face.png]
```

You can add a back face as well:

```
cstm: 1 Card Name [front_face.png] [back_face.png]
```


You may modify the CSV as well to include custom images; Here's a sample line from a CSV.

```
1,Wooded Ridgeline,blc,353
```

This will download the Wooded Ridgeline card from the Bloomburrow Commander set, with collector number 353. However, if you want to insert a custom image, you may add an extra entry:

```
1,Wooded Ridgeline,blc,353,custom/Wooded Ridgeline.png
```

You're still required to have fields for the others, but they don't matter (they can be empty (except for the quantity), like `1,,,,custom/Wooded Ridgeline.png`)

For Double faced cards, you can add another reference to a file:
```
1,Cragcrown Pathway // Timbercrown Pathway,plst,ZNR-261,custom/Cragcrown Pathway.png,custom/Timbercrown Pathway.png
```

You can't add anymore images to a card. If you would like to stitch together a bunch of card images, try the stitch mode.

Archidekt and Moxfield URLs are also accepted.

#### Deck options

Deck mode has many options.

`--include-basic-lands`: includes basic lands

Because of the cheap nature of basic lands, by default they aren't printed out. This will include them anyway.

`--pair-dfc`: Places DFC faces side by side, so they may be folded.

DFC faces by default are places wherever is convenient to not waste paper, and the order of the deck will be preserved -
this will place all DFCs at the start and side by side so they can be folded together.

`--double-sided-mode`: Generates a fully double sided PDF (if there are any DFCs)

The faces may be slightly misaligned, but its within the black card border so its not too bad. 
Definitely worth using if you have special paper that won't be destroyed from that much ink!
These are almost perfectly aligned when using bleed edges, so prefer those if you are able to cut them correctly.

`--back-output`: Generates a second PDF with back faces of DFC cards

This is the same as double sided mode but it outputs every other page in a seperate PDF, which you control the filename of with this option.
You can print all the front faces, then wait for the paper to dry and print all the back faces. This means you can print true DFCs even with
a single sided printer.

