from enum import Enum
from ujson import load, dump
from zoneinfo import ZoneInfo
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.helpers import escape_markdown
from filelock import FileLock

VOLUNTEER_LOCK = FileLock("data/volunteerDetails.json.lock")

class Phase(Enum):
    VOLUNTEER_RECRUITMENT = 0
    REQUEST_PHASE = 1

async def phase_ONE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Change Phase", callback_data = 'phase_TWO')],
        [InlineKeyboardButton("<< Back to Settings", callback_data = "backToSettings")]
    ]

    await query.edit_message_text(
        f"*The bot is currently in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*\
          \n\nWould you like to switch it to the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] != Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\?",
        reply_markup = InlineKeyboardMarkup(keyboard),
        parse_mode = "MarkdownV2"
    )

async def phase_TWO(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("<< Back to Settings", callback_data = "backToSettings")]]

    context.bot_data['PHASE'] = Phase.VOLUNTEER_RECRUITMENT if context.bot_data['PHASE'] == Phase.REQUEST_PHASE else Phase.REQUEST_PHASE

    await query.edit_message_text(
        f"The bot has been successfully switched to the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def ban_ONE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with open('data/userDetails.json') as file:
        userDict = load(file)

    with open('data/banList.json') as file:
        banList = load(file)

    keyboard = []

    for chatID, details in userDict.items():
        if int(chatID) not in banList:
            keyboard.append([InlineKeyboardButton(f"@{details['username']}", callback_data = f"ban_TWO_{details['username']}_{chatID}")])

    keyboard.append([InlineKeyboardButton('<< Back To Settings', callback_data = 'backToSettings')])

    await query.edit_message_text(
        f"Choose the user who you would like to ban.",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def ban_TWO(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    banUsername = parts[-2]
    banChatID = int(parts[-1])

    with VOLUNTEER_LOCK:
        with open('data/volunteerDetails.json') as file:
            volunteerList = load(file)

        volunteerList = [v for v in volunteerList if v != banChatID]

        with open('data/volunteerDetails.json', 'w') as file:
            dump(volunteerList, file, indent = 1)

    with open('data/banList.json') as file:
        banList = load(file)

    banList.append(banChatID)

    with open('data/banList.json', 'w') as file:
        dump(banList, file, indent = 1)

    keyboard = [[InlineKeyboardButton("<< Back to Settings", callback_data = "backToSettings")]]

    await query.edit_message_text(
        f"The user @{escape_markdown(banUsername, version=2)} has been banned.",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def sendEOSReview_ONE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("Yes, send out the survey", callback_data = "sendEOSReview_TWO")],
                [InlineKeyboardButton("<< Back to Settings", callback_data = "backToSettings")]]

    await query.edit_message_text(
        f"Are you sure you would like to send out the EOS survey?",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def sendEOSReview_TWO(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with open('data/userDetails.json') as file:
        userDict = load(file)

    for chatID, details in userDict.items():
        await context.bot.send_message(
            chatID,
            f"Hi {details['fullName']}! As we reach the end of the semester, we would like to receive your feedback on CAPT Care Pal!",
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Leave a review", callback_data = "reviewEOSSTART")]])
        )

    context.bot_data['EOSSURVEY_SENT_TIME'] = datetime.now(ZoneInfo('Asia/Singapore')).strftime('%d %B %Y, %I:%M %p')

    keyboard = [[InlineKeyboardButton("<< Back to Settings", callback_data = "backToSettings")]]

    await query.edit_message_text(
        f"The EOS Survey has been sent out.",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def backToSettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with open('data/userDetails.json') as file:
        userDict = load(file)

    with open('data/banList.json') as file:
        banList = load(file)

    keyboard = [[InlineKeyboardButton("Phase", callback_data = f'phase_ONE')],
                [InlineKeyboardButton("Ban", callback_data = f'ban_ONE')],
                [InlineKeyboardButton("EOS Survey", callback_data = f'sendEOSReview_ONE')]]

    text = f"*The bot is currently in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*\
             \n\n__BANNED USERS__"

    bannedNames = ""

    for chatID in banList:
        bannedNames += f"\n@{escape_markdown(userDict[str(chatID)]['username'], version=2)}"

    if not bannedNames:
        bannedNames = "\nno banned users \U0001F601"

    await query.edit_message_text(
        text + bannedNames,
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard),
    )

PhaseONEInlineHandler = CallbackQueryHandler(phase_ONE, pattern='^phase_ONE$')
PhaseTWOInlineHandler = CallbackQueryHandler(phase_TWO, pattern='^phase_TWO$')
BanONEInlineHandler = CallbackQueryHandler(ban_ONE, pattern='^ban_ONE$')
BanTWOInelineHandler = CallbackQueryHandler(ban_TWO, pattern='^ban_TWO')
SendEOSReviewONEInlineHanlder = CallbackQueryHandler(sendEOSReview_ONE, pattern="^sendEOSReview_ONE$")
SendEOSReviewTWOInlineHanlder = CallbackQueryHandler(sendEOSReview_TWO, pattern="^sendEOSReview_TWO$")
BackToSettingsInlineHandler = CallbackQueryHandler(backToSettings, pattern='^backToSettings$')
