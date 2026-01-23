from ujson import load, dump
from telegram.ext import ContextTypes

async def runDaily(context: ContextTypes.DEFAULT_TYPE):
    # Reset counters
    with open('data/userDetails.json', 'r') as file:
        userDict = load(file)

    for chatID in userDict:
        userDict[chatID]['requestsMade'] = 0

    with open('data/userDetails.json', 'w') as file:
        dump(userDict, file, indent = 1)
