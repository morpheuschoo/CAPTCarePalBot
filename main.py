import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from startup import startup

from individualCommands.start import StartHandler
from individualCommands.help import HelpHandler
from individualCommands.volunteerRegistration import VolunteerRegistrationHandler
from individualCommands.request import RequestHandler
from individualCommands.requestManager import AcceptRequestInlineHandler, CancelRequestInlineHandler, DeclineRequestInlineHandler, CompleteRequestInlineHandler

from groupCommands.settings import PhaseONEInlineHandler, PhaseTWOInlineHandler, BackToSettingsInlineHandler
from groupCommands.broadcast import BroadcastHandler

load_dotenv()

API_KEY = os.getenv("API_KEY")

app = ApplicationBuilder().token(API_KEY).post_init(startup).build()

# Individual Commands
app.add_handler(StartHandler)
app.add_handler(HelpHandler)
app.add_handler(RequestHandler)
app.add_handler(VolunteerRegistrationHandler)

app.add_handler(CancelRequestInlineHandler)
app.add_handler(AcceptRequestInlineHandler)
app.add_handler(DeclineRequestInlineHandler)
app.add_handler(CompleteRequestInlineHandler)

# Group Commands
app.add_handler(BroadcastHandler)

app.add_handler(PhaseONEInlineHandler)
app.add_handler(PhaseTWOInlineHandler)
app.add_handler(BackToSettingsInlineHandler)

app.run_polling()
