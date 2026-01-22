from enum import Enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

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
        f"*The bot has been successfully switched to the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def backToSettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("Phase", callback_data = f'phase_ONE')]]

    await query.edit_message_text(
        f"*The bot is currently in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*\
          \n\nChoose one of the following settings:",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard),
    )

PhaseONEInlineHandler = CallbackQueryHandler(phase_ONE, pattern='^phase_ONE$')
PhaseTWOInlineHandler = CallbackQueryHandler(phase_TWO, pattern='^phase_TWO$')
BackToSettingsInlineHandler = CallbackQueryHandler(backToSettings, pattern='^backToSettings$')
