#!/usr/bin/env python

from inky import InkyPHAT, InkyWHAT
from PIL import Image, ImageFont, ImageDraw
from font_source_sans_pro import SourceSansPro, SourceSansProBold
import time
from datetime import datetime
import requests
import argparse

# Config
inky_display_type = 0 # 0 for InkyPHAT, 1 for InkyWHAT
inky_display_color = "red"

kraken_ticker_url = "https://api.kraken.com/0/public/Ticker"
kraken_ohlc_url = "https://api.kraken.com/0/public/OHLC"
max_api_datapoints = 720 # Max number of datapoints returned by the Kraken API OHLC call (https://stackoverflow.com/questions/48508150/kraken-api-ohlc-request-doesnt-honor-the-since-parameter)

date_time_format = "%d/%m/%Y %H:%M"
currency_thousands_seperator = " "
padding = 5 # padding between edge of container and content. used for graph bounds and graph, screen edge and text,...

# Arguments
parser = argparse.ArgumentParser(description="Crypto ticker with graph for InkyPHAT e-ink display hat. https://github.com/yzwijsen/InkyCryptoGraph")
parser.add_argument("--assetpair", "-p", type=str, default="XXBTZUSD", help="Asset Pair to track. Ex: XXBTZUSD, XXBTZEUR, XETHZUSD,...")
parser.add_argument("--currencysymbol", "-c", type=str, help="Currency symbol should be auto detected, if not you can set it manually.")
parser.add_argument("--range", "-r", type=int, default=1, help="How many days of historical price data to show in the graph.")
parser.add_argument("--holdings", "-ho", type=float, help="Set your holdings. When set the ticker will show the value of your holdings instead of the current crypto price.")
parser.add_argument("--flipscreen","-f", action="store_true", help="Flips the screen 180°.")
parser.add_argument("--verbose", "-v", action="store_true", help="print verbose output.")
parser.add_argument("--blackandwhite", "-bw", action="store_true", help="Only use black and white colors. This reduces the time needed to draw to the display.")
parser.add_argument("--backgroundcolor", "-bgc", type=int, default=0, help="Display background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--graphforegroundcolor", "-gfgc", type=int, default=0, help="Graph foreground color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--graphbackgroundcolor", "-gbgc", type=int, default=1, help="Graph background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--pricecolor", "-pc", type=int, default=1, help="Price color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--textcolor", "-tc", type=int, default=2, help="Price color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--bordercolor", "-bc", type=int, default=1, help="Border color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled.")
parser.add_argument("--linethickness", "-lt", type=int, default=1, help="Graph line thickness in pixels.")
args = parser.parse_args()

#region Functions

def raise_system_exit(error_description, exception_details):
    msg = "Error: " + error_description + " (" + str(exception_details) + ")\nExiting..."
    raise SystemExit(msg)

def get_current_price(pair):
    url = kraken_ticker_url + "?pair=" + pair
    
    # Get ticker data
    try:
        response = requests.get(url)
    except Exception as e:
        raise_system_exit("Kraken API not reachable. Make sure you are connected to the internet and that the Kraken API is up.",e)
    
    # Read JSON response
    try:
        result = response.json()["result"][pair]["c"][0]
    except Exception as e:
        raise_system_exit("Invalid or no JSON response received from Kraken API. Make sure you set a valid asset pair.",e)

    return result

def get_historical_price_data(pair, range, interval):
    # Calculate timestamp for API call
    current_timestamp = time.time()
    since_timestamp = str(int(current_timestamp) - 86400 * range) # subtract x days from current timestamp

    # Get OHLC data
    url = kraken_ohlc_url + "?pair=" + pair + "&interval=" + str(interval) + "&since=" + since_timestamp
    try:
        response = requests.get(url)
    except Exception as e:
        raise_system_exit("Kraken API not reachable. Make sure you are connected to the internet and that the Kraken API is up.",e)

    # Read JSON response
    try:
        prices = response.json()["result"][pair] # 0 = time, 1 = open, 2 = high, 3 = low, 4 = close, 5 = vwap, 6 = volume, 7 = count
    except Exception as e:
        raise_system_exit("Invalid or no JSON response received from Kraken API. Make sure you set a valid asset pair.",e)
    
    # Generate a list with timestamp, high price and low price from OHLC data and convert to int/float
    price_data = []
    for price in prices:
        price_data.append((int(price[0]),float(price[2]),float(price[3]))) # 0 = time, 1 = open, 2 = high, 3 = low, 4 = close, 5 = vwap, 6 = volume, 7 = count

    return price_data

# gets the lowest possible interval to match the requested price history range without passing the max data points threshold of the Kraken API
def get_interval(range, max_datapoints):
    interval_list = [5, 15, 30, 60, 240, 1440, 10080, 21600] # 1 is also a valid option but we're discarding it as it won't even allow us to get 1 day worth of data
    for interval in interval_list:
        datapoints_count = 1440 / interval * range
        if datapoints_count < max_datapoints:
                break
    return interval

# takes a timestamp and price value and plots it within the graph bounds
def plot_graph_point(time,value):
    plot_point_x = int(round(((time - min_time) * delta_screen_x / delta_time + graph_bounds[0][0] + padding)))
    plot_point_y = int(round(((value - min_value) * delta_screen_y / delta_value + graph_bounds[0][1] + padding)))

    # flip the Y value since InkyPHAT screen y-axis is inverted
    plot_point_y = graph_bounds[1][1] - plot_point_y + graph_bounds[0][1]

    return (plot_point_x,plot_point_y)

# Returns rounded and formatted currency as string
def format_price(amount):
    amount = float(amount)
    # Round price and convert to string
    amount = str(round(amount))

    # Add space
    separator_index = len(amount) - 3
    amount = amount[:separator_index] + currency_thousands_seperator + amount[separator_index:]

    # Add currency symbol
    amount = currency_symbol + " " + amount

    return amount

def text_color():
    return inky_display.WHITE if args.blackandwhite else args.textcolor

def price_color():
    return inky_display.WHITE if args.blackandwhite else args.pricecolor

def graph_foreground_color():
    return inky_display.WHITE if args.blackandwhite else args.graphforegroundcolor

def graph_background_color():
    return inky_display.BLACK if args.blackandwhite else args.graphbackgroundcolor

def background_color():
    return inky_display.BLACK if args.blackandwhite else args.backgroundcolor

def border_color():
    return inky_display.WHITE if args.blackandwhite else args.bordercolor

def print_verbose(*messages):
    if args.verbose:
        full_message = ""
        for message in messages:
            full_message += str(message)
            full_message += " "
        print(full_message)

def get_currency_symbol(pair):
    currency_index = len(pair) - 3
    currency = pair[currency_index:]

    if currency == "EUR":
        return "€"
    elif currency == "GBP":
        return "£"
    elif currency == "USD":
        return "$"
    elif currency == "CAD":
        return "$"
    elif currency == "AUD":
        return "$"
    elif currency == "JPY":
        return "¥"
    else:
        return currency

#endregion

# Make sure assetpair is in upper case
args.assetpair = str.upper(args.assetpair)

# Set price history interval so we don't exceed the max amount of data points returned by the Kraken api OHLC call
price_history_interval = get_interval(args.range, max_api_datapoints)

# Set currency symbol
if args.currencysymbol is None:
    currency_symbol = get_currency_symbol(args.assetpair)
else:
    currency_symbol = args.currencysymbol

# Print main parameters
print_verbose("\n#### Parameters ####")
print_verbose("Asset Pair: " + args.assetpair)
print_verbose("Range: " + str(args.range) + " Day(s)")
print_verbose("B&W Mode: " + str(args.blackandwhite))
print_verbose("Flip Screen: " + str(args.flipscreen))
print_verbose("####################\n")

print_verbose("Interval: " + str(price_history_interval) + " (Data Points: " + str(1440 / price_history_interval * args.range) + ")\n")

# Setup fonts
font_small = ImageFont.truetype(SourceSansPro, 12)
font_medium = ImageFont.truetype(SourceSansPro, 16)
font_medium_bold = ImageFont.truetype(SourceSansProBold, 16)
font_large_bold = ImageFont.truetype(SourceSansProBold, 40)

# Initiate Inky display
inky_display = InkyPHAT(inky_display_color) if inky_display_type == 0 else InkyWHAT(inky_display_color)

#inky_display.set_border(inky_display.WHITE)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# When drawing a rectangle accross the entire inkyphat screen the rectangle borders are missing on the screen's right and bottom side (at least on the inkyphat I have)
# To fix this we make the screen a little smaller. Removing one pixel would probably be enough but then we'd have an uneven amount of pixels which would complicate the rest of the code
display_width = inky_display.WIDTH - 2
display_height = inky_display.HEIGHT - 2

# Calculate graph bounds
graph_bounds = [(0,display_height / 2),(display_width / 2,display_height)]

print("Getting price data from Kraken exchange...")

# Get Current Price
current_price = get_current_price(args.assetpair)

# Get Historical price data
historical_price_data = get_historical_price_data(args.assetpair, args.range, price_history_interval)

# Set minmax variables to some initial value from the dataset so we have something to compare to
min_time = max_time = historical_price_data[0][0]
min_value = max_value = historical_price_data[0][1]
low_price = historical_price_data[0][2]

# Calculate min and max values
for i in historical_price_data:
    if i[0] < min_time:
        min_time = i[0]
    if i[0] > max_time:
        max_time = i[0]
    if i[1] < min_value:
        min_value = i[1]
    if i[1] > max_value:
        max_value = i[1]
    # We calculate the low price here as well since we need to use market low instead of market high (which is what we're using for the graph).
    if i[2] < low_price:
        low_price = i[2]

# For the high price we want to use market high, so we just copy max_value
high_price = max_value

# Calculate holdings value instead of price
if args.holdings is not None:
    current_price = float(current_price) * args.holdings
    low_price = float(low_price) * args.holdings
    high_price = float(high_price) * args.holdings

# format prices
current_price = format_price(current_price)
low_price = format_price(low_price)
high_price = format_price(high_price)

print_verbose("Price: " + current_price + "\nLow:   " + low_price + "\nHigh:  " + high_price + "\n")

# Calculate graph dimensions
delta_screen_x = graph_bounds[1][0] - graph_bounds[0][0] - padding * 2
delta_screen_y = graph_bounds[1][1] - graph_bounds[0][1] - padding * 2

# Calculate time & value range
delta_value = max_value - min_value
delta_time = max_time - min_time

# Draw ticker rectangle
draw.rectangle((0,0,display_width,display_height / 2), background_color(), border_color())

# Draw asset pair name
draw.text((padding, 0), args.assetpair, text_color(), font_small)

# Draw current price
w, h = font_large_bold.getsize(current_price)
x = (display_width / 2) - (w / 2)
y = (display_height / 4) - (h / 2)
draw.text((x, y), current_price, price_color(), font_large_bold)

# Draw graph rectangle
draw.rectangle(graph_bounds, graph_background_color(), border_color())

print("Plotting Historical Price Data...")

# Draw graph lines
previous_point = plot_graph_point(historical_price_data[0][0],historical_price_data[0][1])
for i in historical_price_data:
        point = plot_graph_point(i[0],i[1])
        print_verbose(i[0], i[1]," ==> ", point)
        draw.line((previous_point,point),graph_foreground_color(), args.linethickness)
        previous_point = point

print_verbose() # Prints an empty line for prettier verbose output formatting

# Draw details rectangle
draw.rectangle((display_width / 2,display_height / 2,display_width,display_height), background_color(), border_color())

# Set label text
label_high_text = "High:"
label_low_text = "Low:"

# Calculate text size
label_high_width,label_high_height = font_medium.getsize(label_high_text)
label_low_width,label_low_height = font_medium.getsize(label_low_text)
high_price_width,high_price_height = font_medium_bold.getsize(high_price)
low_price_width,low_price_heigth = font_medium_bold.getsize(low_price)

# Calculate positions for labels, top row and bottom row
x_label = (display_width / 2) + padding
y_top = (display_height / 4 * 3) - (display_height / 8) - (label_high_height / 2)
y_bottom = (display_height / 4 * 4) - (display_height / 8) - (label_low_height / 2)

# Draw labels
draw.text((x_label, y_top), label_high_text, text_color(), font_medium)
draw.text((x_label, y_bottom), label_low_text, text_color(), font_medium)

# Draw high price
x = display_width - high_price_width - padding
draw.text((x, y_top), high_price, price_color(), font_medium_bold)

# Draw low price
x = display_width - low_price_width - padding
draw.text((x, y_bottom), low_price, price_color(), font_medium_bold)

# Draw graph time range
draw.text((padding, display_height / 2), str(args.range) + "D", graph_foreground_color(), font_small)

# Draw current datetime
date_time = datetime.now()
date_time_string = date_time.strftime(date_time_format)
w, h = font_small.getsize(date_time_string)
x = display_width - w - padding
draw.text((x, 0), date_time_string, text_color(), font_small)

# Flip img if needed
if args.flipscreen:
    img = img.rotate(180)

# Push image to screen
print("Updating inky display...")
inky_display.set_image(img)
inky_display.show()

print("Done!")