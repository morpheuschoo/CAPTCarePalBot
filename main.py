import os
from ujson import dump
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from volunteerRegistration import VolunteerRegistrationHandler

load_dotenv()
API_KEY = os.getenv("API_KEY")

# create folders
if not os.path.exists("data"):
    os.makedirs("data")

# FIX THIS
if not os.path.exists("data/volunteerDetails.json"):
    with open("data/volunteerDetails.json", 'w') as file:
        dump({}, file, indent = 1)

app = ApplicationBuilder().token(API_KEY).build()

app.add_handler(VolunteerRegistrationHandler)

app.run_polling()
