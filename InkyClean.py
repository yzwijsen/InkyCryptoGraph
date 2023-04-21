#!/usr/bin/env python
# -*- coding: utf-8 -*-

from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
import time

cycles = 3


# Initiate Inky display
inky_display = InkyPHAT("red")

# Create a new canvas to draw on
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))

# Set colours
colours = (inky_display.RED, inky_display.BLACK, inky_display.WHITE)
colour_names = (inky_display.colour, "black", "white")


# Loop through the specified number of cycles and completely
# fill the display with each colour in turn.

for i in range(cycles):
    print("Cleaning cycle %i\n" % (i + 1))
    for j, c in enumerate(colours):
        print("- updating with %s" % colour_names[j])
        inky_display.set_border(c)
        for x in range(inky_display.WIDTH):
            for y in range(inky_display.HEIGHT):
                img.putpixel((x, y), c)
        inky_display.set_image(img)
        inky_display.show()
        time.sleep(1)
    print("\n")

print("Cleaning complete!")
