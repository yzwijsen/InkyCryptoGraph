from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from font_source_sans_pro import SourceSansProBold, SourceSansPro
import time
from datetime import datetime
import requests
import argparse

# Config
DateFormat = "%d/%m/%Y %H:%M"
CurrencyThousandsSeperator = " "
Padding = 5 # padding between edge of container and content. used for graph bounds and graph, screen edge and text,...
MaxAPIDataPoints = 720 # Max number of datapoints returned by the Kraken API OHLC call

# Parse arguments
parser = argparse.ArgumentParser(description="Crypto ticker with graph for InkyPHAT e-ink display hat. https://github.com/yzwijsen/InkyCryptoGraph")
parser.add_argument("--assetpair", "-p", type=str, default="XXBTZUSD", help="Asset Pair to track. Ex: XXBTZUSD, XXBTZEUR,...")
parser.add_argument("--currencysymbol", "-c", type=str, help="Currency symbol should be auto detected, but if not you can set it manually here")
parser.add_argument("--range", "-r", type=int, default=1, help="How many days of historical price data to show in the graph. Maximum is 30 days")
parser.add_argument("--holdings", "-ho", type=float, help="Set your holdings. When set the ticker will show the value of your holdings instead of crypto price")
parser.add_argument("--backgroundcolor", "-bgc", type=int, default=0, help="Display background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--graphforegroundcolor", "-gfgc", type=int, default=0, help="Graph foreground color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--graphbackgroundcolor", "-gbgc", type=int, default=1, help="Graph background color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--pricecolor", "-pc", type=int, default=1, help="Price color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--textcolor", "-tc", type=int, default=2, help="Price color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--bordercolor", "-bc", type=int, default=1, help="Border color. 0 = white, 1 = black, 2 = red/yellow. Ignored when BlackAndWhite mode is enabled")
parser.add_argument("--linethickness", "-lt", type=int, default=1, help="Graph line thickness in pixels")
parser.add_argument("--blackandwhite", "-bw", action="store_true", help="Only use black and white colors")
parser.add_argument("--flipscreen","-f", action="store_true", help="Flips the screen 180°")
parser.add_argument("--verbose", "-v", action="store_true", help="print verbose output")
args = parser.parse_args()

#region Functions

# takes a timestamp and price value and plots it within the graph bounds
def GetPlotPoint(time,value):
    plotPointX = int(round(((time - minTime) * deltaScreenX / deltaTime + GraphBounds[0][0] + Padding)))
    plotPointY = int(round(((value - minValue) * deltaScreenY / deltaValue + GraphBounds[0][1] + Padding)))

    # flip the Y value since InkyPHAT screen y-axis is inverted
    plotPointY = GraphBounds[1][1] - plotPointY + GraphBounds[0][1]

    return (plotPointX,plotPointY)

# Returns rounded and formatted currency as string
def FormatPrice(amount):
    amount = float(amount)
    # Round price and convert to string
    amount = str(round(amount))

    # Add space
    separatorIndex = len(amount) - 3
    amount = amount[:separatorIndex] + CurrencyThousandsSeperator + amount[separatorIndex:]

    # Add currency symbol
    amount = CurrencySymbol + " " + amount

    return amount

def TextColor():
    return inky_display.BLACK if args.blackandwhite else args.textcolor

def PriceColor():
    return inky_display.BLACK if args.blackandwhite else args.pricecolor

def GraphFgColor():
    return inky_display.WHITE if args.blackandwhite else args.graphforegroundcolor

def GraphBgColor():
    return inky_display.BLACK if args.blackandwhite else args.graphbackgroundcolor

def BgColor():
    return inky_display.WHITE if args.blackandwhite else args.backgroundcolor

def BorderColor():
    return inky_display.BLACK if args.blackandwhite else args.bordercolor

def PrintVerbose(*messages):
    if args.verbose:
        finalMessage = ""
        for message in messages:
            finalMessage += str(message)
            finalMessage += " "
        print(finalMessage)

def GetCurrencySymbol(assetPair):
    currencyIndex = len(assetPair) - 3
    currency = assetPair[currencyIndex:]

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

# gets the lowest possible interval to match the requested price history range without passing the max data points threshold of the Kraken API
def GetInterval(range, maxDataPoints):
    intervalList = [5, 15, 30, 60, 240, 1440, 10080, 21600] # 1 is also a valid option but we're discarding it as it isn't even enough to get an entire day's worth of data
    for interval in intervalList:
        dataPoints = 1440 / interval * range
        if dataPoints < maxDataPoints:
                break
    return interval

#endregion


# Make sure assetpair is in upper case
args.assetpair = str.upper(args.assetpair)

# Set price history interval so we don't exceed the max amount of data points returned by the Kraken api OHLC call
priceHistoryInterval = GetInterval(args.range, MaxAPIDataPoints)

# Set currency symbol
if args.currencysymbol is None:
    CurrencySymbol = GetCurrencySymbol(args.assetpair)
else:
    CurrencySymbol = args.currencysymbol

# Print parameters
PrintVerbose("\n#### Parameters ####")
PrintVerbose("Asset Pair: " + args.assetpair)
PrintVerbose("Range: " + str(args.range) + " Day(s)")
PrintVerbose("B&W Mode: " + str(args.blackandwhite))
PrintVerbose("Flip Screen: " + str(args.flipscreen))
PrintVerbose("####################\n")

PrintVerbose("Interval: " + str(priceHistoryInterval) + " (Data Points: " + str(1440 / priceHistoryInterval * args.range) + ")\n")

# Initiate Inky display
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Quick hack
# When drawing a rectangle accross the entire inkyphat screen the rectangle borders are missing on the screen's right and bottom side (at least on the inkyphat I have)
# To fix this we make the screen a little smaller. Removing one pixel would probably be enough but then we'd have an uneven amount of pixels which would complicate the rest of the code
dWidth = inky_display.WIDTH - 2
dHeight = inky_display.HEIGHT - 2

# Set display background color
draw.rectangle((0,0,dWidth,dHeight / 2), BgColor(), BorderColor())

# Calculate graph bounds
GraphBounds = [(0,dHeight / 2),(dWidth / 2,dHeight)]

# Get Current Price
print("Getting price data from Kraken exchange...")
url = "https://api.kraken.com/0/public/Ticker?pair=" + args.assetpair
try:
    response = requests.get(url)
except requests.exceptions.RequestException as e:
    raise SystemExit(e)

currPrice = response.json()["result"][args.assetpair]["c"][0]

# Calculate timestamp for API call
ts = time.time()
timeStamp = str(int(ts) - 86400 * args.range) # subtract x days from current timestamp

# Get historical price data
url = "https://api.kraken.com/0/public/OHLC?pair=" + args.assetpair + "&interval=" + str(priceHistoryInterval) + "&since=" + timeStamp
try:
    response = requests.get(url)
except requests.exceptions.RequestException as e:
    raise SystemExit(e)
    
prices = response.json()["result"][args.assetpair] # 0 = time, 1 = open, 2 = high, 3 = low, 4 = close, 5 = vwap, 6 = volume, 7 = count

# Filter and convert price data
historicalPriceData = []
for price in prices:
    historicalPriceData.append((int(price[0]),float(price[2]),float(price[3]))) # 0 = time, 1 = open, 2 = high, 3 = low, 4 = close, 5 = vwap, 6 = volume, 7 = count

# Set minmax variables to some initial value from the dataset so we have something to compare to
minTime = historicalPriceData[0][0]
maxTime = historicalPriceData[0][0]
minValue = lowPrice = historicalPriceData[0][1]
maxValue = historicalPriceData[0][1]

# Calculate min and max values
for i in historicalPriceData:
    if i[0] < minTime:
        minTime = i[0]
    if i[0] > maxTime:
        maxTime = i[0]
    if i[1] < minValue:
        minValue = i[1]
    if i[1] > maxValue:
        maxValue = i[1]
    # We calculate the low price here as well since we need to use market low instead of market high (which is what we're using for the graph).
    if i[2] < lowPrice:
        lowPrice = i[2]

# For the high price we want to use market high, so we just copy maxValue
highPrice = maxValue

# Calculate holdings value instead of price
if args.holdings is not None:
    currPrice = float(currPrice) * args.holdings
    lowPrice = float(lowPrice) * args.holdings
    highPrice = float(highPrice) * args.holdings

# format prices
currPrice = FormatPrice(currPrice)
lowPrice = FormatPrice(lowPrice)
highPrice = FormatPrice(highPrice)

PrintVerbose("Price: " + currPrice + "\nLow:   " + lowPrice + "\nHigh:  " + highPrice + "\n")

# Calculate graph dimensions
deltaScreenX = GraphBounds[1][0] - GraphBounds[0][0] - Padding * 2
deltaScreenY = GraphBounds[1][1] - GraphBounds[0][1] - Padding * 2

# Calculate time & value range
deltaValue = maxValue - minValue
deltaTime = maxTime - minTime

# Setup fonts
fontSmall = ImageFont.truetype(SourceSansPro, 12)
fontMedium = ImageFont.truetype(SourceSansPro, 16)
fontMediumBold = ImageFont.truetype(SourceSansProBold, 16)
fontLargeBold = ImageFont.truetype(SourceSansProBold, 40)

# Draw asset pair name
draw.text((Padding, 0), args.assetpair, TextColor(), fontSmall)

# Draw current price
w, h = fontLargeBold.getsize(currPrice)
x = (dWidth / 2) - (w / 2)
y = (dHeight / 4) - (h / 2)
draw.text((x, y), currPrice, PriceColor(), fontLargeBold)

# Draw rectangle using graph bounds
draw.rectangle(GraphBounds, GraphBgColor(), BorderColor())

print("Plotting Historical Price Data...")

# Draw graph lines
previousPoint = GetPlotPoint(historicalPriceData[0][0],historicalPriceData[0][1])
for i in historicalPriceData:
        point = GetPlotPoint(i[0],i[1])
        PrintVerbose(i[0], i[1]," ==> ", point)
        draw.line((previousPoint,point),GraphFgColor(), args.linethickness)
        previousPoint = point

PrintVerbose() # Prints an empty line for prettier verbose output formatting

# Draw details rectangle
draw.rectangle((dWidth / 2,dHeight / 2,dWidth,dHeight), BgColor(), BorderColor())

# Set label text
labelHighText = "High:"
labelLowText = "Low:"

# Calculate text size
labelHighWidth,labelHighHeight = fontMedium.getsize(labelHighText)
labelLowWidth,labelLowHeight = fontMedium.getsize(labelLowText)
highPriceWidth,highPriceHeight = fontMediumBold.getsize(highPrice)
lowPriceWidth,lowPriceHeight = fontMediumBold.getsize(lowPrice)

# Calculate positions for labels, top row and bottom row
xLabel = (dWidth / 2) + Padding
yTop = (dHeight / 4 * 3) - (dHeight / 8) - (labelHighHeight / 2)
yBottom = (dHeight / 4 * 4) - (dHeight / 8) - (labelLowHeight / 2)

# Draw labels
draw.text((xLabel, yTop), labelHighText, TextColor(), fontMedium)
draw.text((xLabel, yBottom), labelLowText, TextColor(), fontMedium)

# Draw high price
x = dWidth - highPriceWidth - Padding
draw.text((x, yTop), highPrice, PriceColor(), fontMediumBold)

# Draw low price
x = dWidth - lowPriceWidth - Padding
draw.text((x, yBottom), lowPrice, PriceColor(), fontMediumBold)

# Draw graph time range
draw.text((Padding, dHeight / 2), str(args.range) + "D", GraphFgColor(), fontSmall)

# Draw current datetime
now = datetime.now()
dt_string = now.strftime(DateFormat)
w, h = fontSmall.getsize(dt_string)
x = dWidth - w - Padding
draw.text((x, 0), dt_string, TextColor(), fontSmall)

# Flip img if needed
if args.flipscreen:
    img = img.rotate(180)

# Push image to screen
print("Updating inkyPHAT display...")
inky_display.set_image(img)
inky_display.show()

print("Done!")
