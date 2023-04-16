# InkyCryptoGraph :chart_with_upwards_trend::money_with_wings:

[![GitHub license](https://img.shields.io/github/license/yzwijsen/InkyCryptoGraph)](https://github.com/yzwijsen/InkyCryptoGraph/blob/main/LICENSE)

Customizable crypto ticker and graph for Pimoroni InkyPHAT e-ink display hat.

Default Colors             |  Dark mode
:-------------------------:|:-------------------------:
![Example picture 2](https://i.imgur.com/gshzbpWl.jpg)  |  ![Example picture 1](https://i.imgur.com/VVFmSCel.jpg)

## :scroll: Description
InkyCryptoGraph is a Python script that fetches cryptocurrency data from the Kraken Exchange API and displays it on an InkyPHAT or InkyWHAT e-ink display hat for Raspberry Pi. The script can display the current price, low, high, and a historical price graph.

## :wrench: Pre-requisites
* [Raspberry Pi](https://www.raspberrypi.org/products/) with [InkyPHAT](https://shop.pimoroni.com/products/inky-phat) or [InkyWHAT](https://shop.pimoroni.com/products/inky-what) e-ink display hat
* Python 3.x
* [inky](https://github.com/pimoroni/inky) library by Pimoroni
* [Pillow](https://pillow.readthedocs.io/en/stable/) library
* Internet connection for fetching price data

## :inbox_tray: Installation
1. Clone this repository: `git clone https://github.com/yzwijsen/InkyCryptoGraph.git`
2. Install required libraries:
   - using pip: `pip install inky Pillow`
   - manually: `curl https://get.pimoroni.com/inky | bash` (Full instructions [here](https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-inky-phat))
3. Run the script: `python InkyCryptoGraph.py`

## :gear: Parameters
The script accepts various command line arguments to customize the output:

| Parameter             | Description                                                                              |
|-----------------------|------------------------------------------------------------------------------------------|
| `--assetpair` `-p`    | Asset Pair to track. Ex: XXBTZUSD, XXBTZEUR, XETHZUSD, ...                               |
| `--currencysymbol` `-c`| Currency symbol should be auto detected, if not you can set it manually.                 |
| `--range` `-r`        | How many days of historical price data to show in the graph.                             |
| `--holdings` `-ho`    | Set your holdings. When set the ticker will show the value of your holdings instead of the current crypto price.|
| `--flipscreen` `-f`   | Flips the screen 180°.                                                                   |
| `--verbose` `-v`      | Print verbose output.                                                                    |
| `--blackandwhite` `-bw`| Only use black and white colors. This reduces the time needed to draw to the display.    |
| `--backgroundcolor` `-bgc`| Display background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.|
| `--graphforegroundcolor` `-gfgc`| Graph foreground color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.|
| `--graphbackgroundcolor` `-gbgc`| Graph background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.|
| `--pricecolor` `-pc`  | Price color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.|
| `--textcolor` `-tc`   | Price color. 0 = white, 1 = black, 2.|
| `--bordercolor` `-pc`  | Border color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.|
| `--linethickness` `-tc`   | Graph line thickness in pixels.|


