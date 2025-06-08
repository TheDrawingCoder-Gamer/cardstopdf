# Cards to PDF

converts cards to pdf

because of how bad of a format pdf is i found that a single page takes ~20s. This means a full commander deck with all unique cards would take
4 minutes to generate. Have fun with that!

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


### Stitch mode

Just pass in the directory of the deck as the first argument to the stitch mode:

```
python main.py --output out.pdf stitch input_dir
```

All images in the directory will be put on the page. It's assumed the images are in the correct aspect ratio, and stretching/clipping
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

The faces may be slightly misaligned, but its within the black card border so its not too bad. Definitely worth using if you have special paper that won't be
destroyed from that much ink!


