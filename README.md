# InkyCryptoGraph :chart_with_upwards_trend::money_with_wings:

[![GitHub Super-Linter](https://github.com/yzwijsen/InkyCryptoGraph/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)
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
* [Inky](https://github.com/pimoroni/inky) library by Pimoroni
* [Pillow](https://pillow.readthedocs.io/en/stable/) library

## :inbox_tray: Installation
1. Clone this repository: `git clone https://github.com/yzwijsen/InkyCryptoGraph.git`
2. Install required libraries:
   - using pip: `pip install inky Pillow`
   - manually: `curl https://get.pimoroni.com/inky | bash` (Full instructions [here](https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-inky-phat))
3. Run the script: `python3 /home/pi/InkyCryptoGraph.py -p XXBTZEUR -r 1`
4. Setup Cron to run the script every x minutes

## :recycle: Cleaning script

I have included a modified version of the Pimoroni Inky cleaning script.
This script should be ran once in a while to keep the screen in good condition. It does this by running through all the colors and overwriting the entire screen.
This will keep your screen in good condition and reduce artifacts / ghosting.

> **Note**
> You can include the cleaning script in your crontab file to have it run automatically, just make sure that it doesn't overlap with the main script. Otherwise the screen will stop updating untill you restart the main script. A window of 15 minutes should be more than enough to run the cleaning script.
> 
> The included crontab example already has an entry for this cleaning script.

## :clock7: Cron / Scheduling

To keep the screen updated you can setup a cron job to run the script every x minutes
You can set this up by running `crontab -e` and adding an entry for the main script and, optionally, the cleaning script.

Below is an example configuration. You can also find this in the **crontab** file included in this repository.

```cron
*/5 8-23 * * * python3 /home/pi/InkyCryptoGraph.py -p XXBTZEUR -f -r 1
*/5 0-2 * * * python3 /home/pi/InkyCryptoGraph.py -p XXBTZEUR -f -bw -r 1
*/30 3-7 * * * python3 /home/pi/InkyCryptoGraph.py -p XXBTZEUR -f -bw -r 1
45 6 * * * python3 /home/pi/InkyClean.py
```

This crontab file will run the script in color mode every 5 minutes from 8AM till 11PM.
The rest of the time it will run in dark mode. We're also lowering the update time to every 30 minutes between 3AM and 7AM.
Finally, we run the cleaning script once every day at 6:45 AM

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

