from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from font_source_sans_pro import SourceSansProBold
import time
from datetime import datetime
import requests

# Config
GraphBounds = [(0,52),(106,104)] # This defines the bounds for the graph // default: [(0,0),(212,104)]
Padding = 5
PriceHistoryRange = 1 # in days
PriceHistoryInterval = 60 # in minutes
AssetPair = "XXBTZEUR"
CurrencySymbol = "€"
CurrencyThousandsSeperator = " "
FlipScreen = False


def GetPlotPoint(time,value):
    plotPointX = int(round(((time - minTime) * deltaScreenX / deltaTime + GraphBounds[0][0] + Padding)))
    plotPointY = int(round(((value - minValue) * deltaScreenY / deltaValue + GraphBounds[0][1] + Padding)))

    # flip the Y value since InkyPHAT screen y-axis is inverted
    plotPointY = GraphBounds[1][1] - plotPointY + GraphBounds[0][1]

    return (plotPointX,plotPointY)

def FormatPrice(amount):
    amount = float(amount)
    # Round price and convert to string
    amount = str(int(round(amount)))

    # Add space
    separatorIndex = len(amount) - 3
    amount = amount[:separatorIndex] + CurrencyThousandsSeperator + amount[separatorIndex:]

    # Add currency symbol
    amount = CurrencySymbol + " " + amount

    return amount


# Get Current Price
url = "https://api.kraken.com/0/public/Ticker?pair=" + AssetPair
response = requests.get(url)
currPrice = response.json()["result"][AssetPair]["c"][0]


# Calculate timestamp for API call
ts = time.time()
timeStamp = str(int(ts) - 86400 * PriceHistoryRange) # subtract 7 days from current timestamp

# Get historical price data
url = "https://api.kraken.com/0/public/OHLC?pair=" + AssetPair + "&interval=" + str(PriceHistoryInterval) + "&since=" + timeStamp
response = requests.get(url)
prices = response.json()["result"][AssetPair]

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
    # We need to calculate the low price separately since minValue is based on the market high instead of market low.
    if i[2] < lowPrice:
        lowPrice = i[2]

# high price does not need to be calculated since it's the same as maxValue
highPrice = maxValue

# format prices
currPrice = FormatPrice(currPrice)
lowPrice = FormatPrice(lowPrice)
highPrice = FormatPrice(maxValue)

print("Price: " + currPrice, "\nLow:   " + lowPrice, "\nHigh:  " + highPrice)

# Calculate graph dimensions
deltaScreenX = GraphBounds[1][0] - GraphBounds[0][0] - Padding * 2
deltaScreenY = GraphBounds[1][1] - GraphBounds[0][1] - Padding * 2

# Calculate time & value range
deltaValue = maxValue - minValue
deltaTime = maxTime - minTime

# Initiate Inky display
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.BLACK)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Set default font
fontSmall = ImageFont.truetype(SourceSansProBold, 12)
fontMedium = ImageFont.truetype(SourceSansProBold, 16)
fontLarge = ImageFont.truetype(SourceSansProBold, 36)

# Draw AssetPair
draw.text((Padding, 0), AssetPair, inky_display.RED, fontSmall)

# Draw current price
w, h = fontLarge.getsize(currPrice)
x = (inky_display.WIDTH / 2) - (w / 2)
y = (inky_display.HEIGHT / 4) - (h / 2)
draw.text((x, y), currPrice, inky_display.BLACK, fontLarge)

#draw rectangle using graph bounds
draw.rectangle(GraphBounds, inky_display.RED, inky_display.BLACK)

print("Plotting Historical Price Data...")

# Calculate plot points
previousPoint = GetPlotPoint(historicalPriceData[0][0],historicalPriceData[0][1])
for i in historicalPriceData:
        point = GetPlotPoint(i[0],i[1])
        print(i[0], i[1]," ==> ", point)
        draw.line((previousPoint,point),inky_display.WHITE, 1)
        previousPoint = point

# Draw details rectangle
draw.rectangle((inky_display.WIDTH / 2,inky_display.HEIGHT / 2,inky_display.WIDTH,inky_display.HEIGHT), inky_display.WHITE, inky_display.BLACK)
draw.text((inky_display.WIDTH / 2 + Padding, 55), "High:", inky_display.RED, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding + 40, 65), highPrice, inky_display.BLACK, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding, 80), "Low:", inky_display.RED, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding + 40, 90), lowPrice, inky_display.BLACK, fontSmall)

# Draw graph time range
draw.text((Padding, inky_display.HEIGHT / 2 + Padding), str(PriceHistoryRange) + "D", inky_display.WHITE, fontSmall)

# Draw current datetime
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M")
w, h = fontSmall.getsize(dt_string)
x = (inky_display.WIDTH) - w - Padding
draw.text((x, 0), dt_string, inky_display.RED, fontSmall)

print("Drawing to screen...")

# Push image to screen
if FlipScreen:
    img = img.rotate(180)

inky_display.set_image(img)
inky_display.show()
