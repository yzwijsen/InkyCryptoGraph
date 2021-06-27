from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne
from font_hanken_grotesk import HankenGrotesk
from font_source_sans_pro import SourceSansProBold, SourceSansPro
import time
from datetime import datetime
import requests
import argparse

# Config
CurrencyThousandsSeperator = " "
Padding = 5 # padding between edge of container and content. used for graph bounds and graph, screen edge and text,...
PriceHistoryInterval = 60 # in minutes. (lower interval means more data points and thus a more detailed graph)
GraphColors = (0,1) # (ForegroundColor, BackgroundColor) // 0 = white, 1 = black, 2 = red // Ignored when BlackAndWhite mode is set to True
GraphLineThickness = 1 # in pixels

# Parse arguments
parser = argparse.ArgumentParser(description="Crypto ticker with graph for InkyPHAT e-ink display hat")
parser.add_argument("--assetpair", "-p", type=str, default="XXBTZUSD", help="Asset Pair to track. Ex: XXBTZUSD, XXBTZEUR,...")
parser.add_argument("--currencysymbol", "-c", type=str, help="Currency symbol should be auto detected, but if not you can set it manually here")
parser.add_argument("--range", "-r", type=int, default=1, help="How many days of historical price data to show in the graph")
parser.add_argument("--blackandwhite", "-bw", action="store_true", help="Only use black and white colors")
parser.add_argument("--flipscreen","-f", action="store_true", help="Flips the screen 180°")
parser.add_argument("--verbose", "-v", action="store_true", help="print verbose output")
args = parser.parse_args()

# Make sure assetpair is in upper case
args.assetpair = str.upper(args.assetpair)

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

def HighlightColor():
    return inky_display.BLACK if args.blackandwhite else inky_display.RED

def GraphFgColor():
    return inky_display.WHITE if args.blackandwhite else GraphColors[0]

def GraphBgColor():
    return inky_display.BLACK if args.blackandwhite else GraphColors[1]

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

# Print parameters
PrintVerbose("\n#### Parameters ####")
PrintVerbose("Asset Pair: " + args.assetpair)
PrintVerbose("Range: " + str(args.range) + " Day(s)")
PrintVerbose("B&W Mode: " + str(args.blackandwhite))
PrintVerbose("Flip Screen: " + str(args.flipscreen))
PrintVerbose("####################\n")

# Set currency symbol
if args.currencysymbol is None:
    CurrencySymbol = GetCurrencySymbol(args.assetpair)
else:
    CurrencySymbol = args.currencysymbol

# Initiate Inky display
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.BLACK)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Calculate graph bounds
GraphBounds = [(0,inky_display.HEIGHT / 2),(inky_display.WIDTH / 2,inky_display.HEIGHT)]

# Get Current Price
print("Getting price data from Kraken exchange...")
url = "https://api.kraken.com/0/public/Ticker?pair=" + args.assetpair
response = requests.get(url)
currPrice = response.json()["result"][args.assetpair]["c"][0]

# Calculate timestamp for API call
ts = time.time()
timeStamp = str(int(ts) - 86400 * args.range) # subtract x days from current timestamp

# Get historical price data
url = "https://api.kraken.com/0/public/OHLC?pair=" + args.assetpair + "&interval=" + str(PriceHistoryInterval) + "&since=" + timeStamp
response = requests.get(url)
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

# Set default font
fontSmall = ImageFont.truetype(SourceSansPro, 12)
fontMedium = ImageFont.truetype(SourceSansPro, 16)
fontMediumBold = ImageFont.truetype(SourceSansProBold, 16)
fontLargeBold = ImageFont.truetype(SourceSansProBold, 40)

# Draw asset pair name
draw.text((Padding, 0), args.assetpair, HighlightColor(), fontSmall)

# Draw current price
w, h = fontLargeBold.getsize(currPrice)
x = (inky_display.WIDTH / 2) - (w / 2)
y = (inky_display.HEIGHT / 4) - (h / 2)
draw.text((x, y), currPrice, inky_display.BLACK, fontLargeBold)

# Draw rectangle using graph bounds
draw.rectangle(GraphBounds, GraphBgColor(), inky_display.BLACK)

print("Plotting Historical Price Data...")

# Calculate plot points
previousPoint = GetPlotPoint(historicalPriceData[0][0],historicalPriceData[0][1])
for i in historicalPriceData:
        point = GetPlotPoint(i[0],i[1])
        PrintVerbose(i[0], i[1]," ==> ", point)
        draw.line((previousPoint,point),GraphFgColor(), GraphLineThickness)
        previousPoint = point

PrintVerbose() # Prints an empty line for prettier verbose output formatting

# Draw details rectangle
draw.rectangle((inky_display.WIDTH / 2,inky_display.HEIGHT / 2,inky_display.WIDTH,inky_display.HEIGHT), inky_display.WHITE, inky_display.BLACK)

# Set label text
labelHighText = "High:"
labelLowText = "Low:"

# Calculate text size
labelHighWidth,labelHighHeight = fontMedium.getsize(labelHighText)
labelLowWidth,labelLowHeight = fontMedium.getsize(labelLowText)
highPriceWidth,highPriceHeight = fontMediumBold.getsize(highPrice)
lowPriceWidth,lowPriceHeight = fontMediumBold.getsize(lowPrice)

# Calculate label, top row and bottom row locations
xLabel = (inky_display.WIDTH / 2) + Padding
yTop = (inky_display.HEIGHT / 4 * 3) - (inky_display.HEIGHT / 8) - (labelHighHeight / 2)
yBottom = (inky_display.HEIGHT / 4 * 4) - (inky_display.HEIGHT / 8) - (labelLowHeight / 2)

# Draw labels
draw.text((xLabel, yTop), labelHighText, HighlightColor(), fontMedium)
draw.text((xLabel, yBottom), labelLowText, HighlightColor(), fontMedium)

# Draw high price
x = inky_display.WIDTH - highPriceWidth - Padding
draw.text((x, yTop), highPrice, inky_display.BLACK, fontMediumBold)

# Draw low price
x = inky_display.WIDTH - lowPriceWidth - Padding
draw.text((x, yBottom), lowPrice, inky_display.BLACK, fontMediumBold)

# Draw graph time range
draw.text((Padding, inky_display.HEIGHT / 2), str(args.range) + "D", GraphFgColor(), fontSmall)

# Draw current datetime
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M")
w, h = fontSmall.getsize(dt_string)
x = (inky_display.WIDTH) - w - Padding
draw.text((x, 0), dt_string, HighlightColor(), fontSmall)

# Flip img if needed
if args.flipscreen:
    img = img.rotate(180)

# Push image to screen
print("Updating inkyPHAT display...")
inky_display.set_image(img)
inky_display.show()

print("Done!")
