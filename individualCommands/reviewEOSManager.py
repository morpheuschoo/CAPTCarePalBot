from ujson import load, dump
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from filelock import FileLock

EOSSURVEY_LOCK = FileLock("data/eosSurvey.json.lock")

async def reviewEOS_START(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("Yes, it helped me recieve help when I needed it", callback_data = "reviewEOSOPENENDED_0")],
                [InlineKeyboardButton("Yes, it made it easier for me to help others", callback_data = "reviewEOSOPENENDED_1")],
                [InlineKeyboardButton("Somewhat, I didn't use it much", callback_data = "reviewEOSOPENENDED_2")],
                [InlineKeyboardButton("No, it didn't make a difference for me", callback_data = "reviewEOSOPENENDED_3")]]

    await query.edit_message_text(text = query.message.text_markdown_v2, parse_mode = "MarkdownV2", reply_markup = None)
    await context.bot.send_message(
        query.from_user.id,
        f"Did CAPT Care Pal help strengthen mutual care in CAPT (eg. making it easier to give/receive help) ?",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def reviewEOS_OPEN_ENDED(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    option = ["Yes, it helped me recieve help when I needed it",
              "Yes, it made it easier for me to help others",
              "Somewhat, I didn't use it much",
              "No, it didn't make a difference for me"][int(query.data.split("_")[-1])]

    context.user_data['REVIEW_EOS_INFO'] = {'option': option, 'prevMsgID': query.message.message_id}

    await query.edit_message_text(
        text = "Any other feedback for us? Feel free to share what worked well or what should we improve\\.\n\n_*Please type your reply in one message*_",
        parse_mode = "MarkdownV2",
        reply_markup = None
    )

    context.user_data['AWAITING_REVIEW_EOS_COMMENT'] = True

# Review EOS Comment Handler in reviewRequestManager.py --> ReviewCommentHandler

ReviewEOSSTARTInlineHandler = CallbackQueryHandler(reviewEOS_START, pattern='^reviewEOSSTART$')
ReviewEOSOPENENDEDInlineHandler = CallbackQueryHandler(reviewEOS_OPEN_ENDED, pattern='^reviewEOSOPENENDED')
