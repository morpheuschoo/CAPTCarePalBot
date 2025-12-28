import os
from ujson import dump
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from start import StartHandler
from help import HelpHandler
from volunteerRegistration import VolunteerRegistrationHandler
from request import RequestHandler

def makeFolders():
    if not os.path.exists("data"):
        os.makedirs("data")

    list_files = ["volunteerDetails.json"]
    dict_files = ["userDetails.json"]

    for filename in list_files:
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as file:
                dump([], file, indent = 1)

    for filename in dict_files:
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as file:
                dump({}, file, indent = 1)

makeFolders()

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = ApplicationBuilder().token(API_KEY).build()

app.add_handler(StartHandler)
app.add_handler(HelpHandler)
app.add_handler(RequestHandler)
app.add_handler(VolunteerRegistrationHandler)

app.run_polling()
