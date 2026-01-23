import os
from datetime import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from startup import startup
from runDaily import runDaily

from individualCommands.start import StartHandler
from individualCommands.help import HelpHandler
from individualCommands.volunteerRegistration import VolunteerRegistrationHandler
from individualCommands.request import RequestHandler
from individualCommands.requestManager import AcceptRequestInlineHandler, CancelRequestInlineHandler, RemoveRequestInlineHandler, DeclineRequestInlineHandler, CompleteRequestInlineHandler
from individualCommands.reviewRequestManager import ReviewCommentHandler, ReviewRequestSTARTInlineHandler, ReviewRequestSELECTIONInlineHandler, ReviewRequestSAVESELECTIONInlineHandler, ReviewRequestOPENENDEDInlineHandler
from individualCommands.reviewEOSManager import ReviewEOSSTARTInlineHandler, ReviewEOSOPENENDEDInlineHandler

from groupCommands.information import runInformation
from groupCommands.settings import SendEOSReviewONEInlineHanlder, SendEOSReviewTWOInlineHanlder, BanONEInlineHandler, BanTWOInelineHandler, PhaseONEInlineHandler, PhaseTWOInlineHandler, BackToSettingsInlineHandler
from groupCommands.broadcast import BroadcastHandler, ConfirmBroadcastInlineHandler, CancelBroadcastInlineHandler

load_dotenv()

API_KEY = os.getenv("API_KEY")

app = ApplicationBuilder().token(API_KEY).post_init(startup).build()

# Individual Commands
app.add_handler(StartHandler)
app.add_handler(HelpHandler)
app.add_handler(RequestHandler)
app.add_handler(VolunteerRegistrationHandler)
app.add_handler(ReviewCommentHandler)

app.add_handler(CancelRequestInlineHandler)
app.add_handler(RemoveRequestInlineHandler)
app.add_handler(AcceptRequestInlineHandler)
app.add_handler(DeclineRequestInlineHandler)
app.add_handler(CompleteRequestInlineHandler)
app.add_handler(ReviewRequestSTARTInlineHandler)
app.add_handler(ReviewRequestSELECTIONInlineHandler)
app.add_handler(ReviewRequestSAVESELECTIONInlineHandler)
app.add_handler(ReviewRequestOPENENDEDInlineHandler)
app.add_handler(ReviewEOSSTARTInlineHandler)
app.add_handler(ReviewEOSOPENENDEDInlineHandler)

# Group Commands
app.add_handler(BroadcastHandler)

app.add_handler(ConfirmBroadcastInlineHandler)
app.add_handler(CancelBroadcastInlineHandler)
app.add_handler(PhaseONEInlineHandler)
app.add_handler(PhaseTWOInlineHandler)
app.add_handler(BanONEInlineHandler)
app.add_handler(BanTWOInelineHandler)
app.add_handler(SendEOSReviewONEInlineHanlder)
app.add_handler(SendEOSReviewTWOInlineHanlder)
app.add_handler(BackToSettingsInlineHandler)

app.job_queue.run_daily(runDaily, time = time(hour = 0, minute = 0, tzinfo = ZoneInfo('Asia/Singapore')))
app.job_queue.run_repeating(runInformation, interval = 300)

app.run_polling()
