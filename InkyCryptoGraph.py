from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne
import time
from datetime import datetime
import requests

# Config
GraphBounds = [(0,52),(106,104)] # This defines the bounds for the graph // default: [(0,0),(212,104)]
Padding = 5
PriceHistoryInDays = 1
PriceHistoryInterval = 60
AssetPair = "XXBTZEUR"
CurrencySymbol = "€"


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
    spaceIndex = len(amount) - 3
    amount = amount[:spaceIndex] + " " + amount[spaceIndex:]

    # Add currency symbol
    amount = CurrencySymbol + " " + amount

    return amount


# Get Current Price
url = "https://api.kraken.com/0/public/Ticker?pair=" + AssetPair
response = requests.get(url)
currPrice = response.json()["result"][AssetPair]["c"][0]
lowPrice = response.json()["result"][AssetPair]["l"][1]
highPrice = response.json()["result"][AssetPair]["h"][1]

# format prices
currPrice = FormatPrice(currPrice)
lowPrice = FormatPrice(lowPrice)
highPrice = FormatPrice(highPrice)

print("Price:    " + currPrice, "\n24H Low:  " + lowPrice, "\n24H High: " + highPrice)

# Calculate timestamp for API call
ts = time.time()
#timeStamp = str(int(ts) - 86400) # subtract 24hrs from current timestamp
timeStamp = str(int(ts) - 86400 * PriceHistoryInDays) # subtract 7 days from current timestamp

# Get historical price data
url = "https://api.kraken.com/0/public/OHLC?pair=xbteur&interval=" + str(PriceHistoryInterval) + "&since=" + timeStamp
response = requests.get(url)
prices = response.json()["result"][AssetPair]

rawData = []

for price in prices:
    rawData.append((int(price[0]),float(price[2]))) # 0 = time, 1 = open, 2 = high, 3 = low, 4 = close, 5 = vwap, 6 = volume, 7 = count

# Set minmax variables to some initial value from the dataset so we have something to compare to
minTime = rawData[0][0]
maxTime = rawData[0][0]
minValue = rawData[0][1]
maxValue = rawData[0][1]

# Calculate min and max time & value
for i in rawData:
    if i[0] < minTime:
        minTime = i[0]
    if i[0] > maxTime:
        maxTime = i[0]
    if i[1] < minValue:
        minValue = i[1]
    if i[1] > maxValue:
        maxValue = i[1]

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
fontSmall = ImageFont.truetype(FredokaOne, 12)
fontMedium = ImageFont.truetype(FredokaOne, 16)
fontLarge = ImageFont.truetype(FredokaOne, 36)

# Draw header
message = "btc"
draw.text((Padding, 0), message, inky_display.RED, fontSmall)

# Draw current price
message = currPrice
w, h = fontLarge.getsize(message)
x = (inky_display.WIDTH / 2) - (w / 2)
y = (inky_display.HEIGHT / 4) - (h / 2)
draw.text((x, y), message, inky_display.BLACK, fontLarge)

#draw rectangle using graph bounds
draw.rectangle(GraphBounds, inky_display.RED, inky_display.BLACK)

print("Plotting Historical Price Data...")

# Calculate plot points
previousPoint = GetPlotPoint(rawData[0][0],rawData[0][1])
for i in rawData:
        point = GetPlotPoint(i[0],i[1])
        print(i[0], i[1]," ==> ", point)
        draw.line((previousPoint,point),inky_display.WHITE, 2)
        previousPoint = point

# Draw details rectangle
draw.rectangle((inky_display.WIDTH / 2,inky_display.HEIGHT / 2,inky_display.WIDTH,inky_display.HEIGHT), inky_display.WHITE, inky_display.BLACK)
draw.text((inky_display.WIDTH / 2 + Padding, 55), "High:", inky_display.RED, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding + 40, 65), highPrice, inky_display.BLACK, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding, 80), "Low:", inky_display.RED, fontSmall)
draw.text((inky_display.WIDTH / 2 + Padding + 40, 90), lowPrice, inky_display.BLACK, fontSmall)

# Draw graph time range
draw.text((Padding, inky_display.HEIGHT / 2 + Padding), str(PriceHistoryInDays) + "D", inky_display.WHITE, fontSmall)

# Draw current datetime
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M")
w, h = fontSmall.getsize(dt_string)
x = (inky_display.WIDTH) - w - Padding
draw.text((x, 0), dt_string, inky_display.RED, fontSmall)

print("Drawing to screen...")

# Push image to screen
inky_display.set_image(img)
inky_display.show()
