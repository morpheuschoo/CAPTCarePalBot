from enum import Enum
from ujson import load, dump
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from filelock import FileLock

DEAD_LOCK = FileLock("data/deadRequests.json.lock")

class Rating(Enum):
    VERY_POOR = 0
    POOR = 1
    AVERAGE = 2
    GOOD = 3
    VERY_GOOD = 4

async def reviewRequest_START(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['']

    parts = query.data.split('_')
    role = parts[1]
    requestID = parts[2]

    keyboard = [[InlineKeyboardButton("Very Poor", callback_data = f'reviewRequestSELECTION_{requestID}_{role}_{Rating.VERY_POOR}')],
                [InlineKeyboardButton("Poor", callback_data = f'reviewRequestSELECTION_{requestID}_{role}_{Rating.POOR}')],
                [InlineKeyboardButton("Average", callback_data = f'reviewRequestOPENENDED_{requestID}_{role}_{Rating.AVERAGE}')],
                [InlineKeyboardButton("Good", callback_data = f'reviewRequestOPENENDED_{requestID}_{role}_{Rating.GOOD}')],
                [InlineKeyboardButton("Very Good", callback_data = f'reviewRequestOPENENDED_{requestID}_{role}_{Rating.VERY_GOOD}')]]

    await query.edit_message(reply_markup = None)
    await context.bot.send_message(
        query.from_user.id,
        f"Leaving a review for request *ID* \\#{requestID}\n\nPlease rate your experience",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def reviewRequest_SELECTION(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    requestID = parts[1]
    role = parts[2]
    rating = int(parts[3])

    if role == 'requester':
        keyboard = [[InlineKeyboardButton("Slow response", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_0')],
                    [InlineKeyboardButton("Volunteer did not address my need", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_1')],
                    [InlineKeyboardButton("Volunteer was impolite/disrespectful", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_2')],
                    [InlineKeyboardButton("None of the above", callback_data = f'reviewRequestOPENENDED_{requestID}_{role}_{rating}')]]
    elif role == 'acceptor':
        keyboard = [[InlineKeyboardButton("Request details were unclear/incomplete", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_0')],
                    [InlineKeyboardButton("Requester was unresponsive", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_1')],
                    [InlineKeyboardButton("Coordination took too long", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_2')],
                    [InlineKeyboardButton("I didn't feel respected/comfortable", callback_data = f'reviewRequestSAVESELECTION_{requestID}_{role}_{rating}_3')],
                    [InlineKeyboardButton("None of the above", callback_data = f'reviewRequestOPENENDED_{requestID}_{role}_{rating}')]]

    await query.edit_message_text(
        f"Leaving a review for request *ID* \\#{requestID}\
          \n\nWe're sorry that the experience wasn't great\\. What was the main issue?",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def reviewRequest_SAVE_SELECTION(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    requestID = parts[1]
    role = parts[2]
    rating = int(parts[3])
    commentID = int(parts[4])
    comments = None

    if role == 'requester':
        match commentID:
            case 0:
                comments = "Slow response"
            case 1:
                comments = "Volunteer did not address my need"
            case 2:
                comments = "Volunteer was impolite/disrespectful"
    elif role == 'acceptor':
        match commentID:
            case 0:
                comments = "Request details were unclear/incomplete"
            case 1:
                comments = "Requester was unresponsive"
            case 2:
                comments = "Coordination took too long"
            case 3:
                comments = "I didn't feel respected/comfortable"
    with DEAD_LOCK:
        with open('data/deadRequests.json', 'r') as file:
            deadRequestsDict = load(file)

        deadRequestsDict[requestID]['reviews'][role] = {'rating': rating, 'comments': comments}

        with open('data/deadRequests.json', 'w') as file:
            dump(deadRequestsDict, file, indent = 1)

    await query.edit_message_text(
        f"We have recorded your review for request *ID* \\#{requestID}\\.\
        \n\nThank you for your feedback\\.",
        parse_mode = "MarkdownV2",
        reply_markup = None
    )

async def reviewRequest_OPEN_ENDED(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    requestID = parts[1]
    role = parts[2]
    rating = int(parts[3])

    context.user_data['AWAITING_REVIEW_REQUEST_COMMENT'] = True
    context.user_data['REVIEW_REQUEST_INFO'] = {
        'requestID': requestID,
        'role': role,
        'rating': rating,
        'prevMsgID': query.message.message_id
    }

    text = f"Leaving a review for request *ID* \\#{requestID}\n\n"

    if rating < Rating.AVERAGE.value:
        text += "Could you tell us what was the main issue? \\(type it in one message\\)"
    else:
        text += "Could you share with us what was helpful or smooth? \\(type it in one message)"

    await query.edit_message_text(
        text,
        parse_mode = "MarkdownV2",
        reply_markup = None,
    )

async def ReviewRequestComment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data['AWAITING_REVIEW_REQUEST_COMMENT']:
        return

    chatID = update.effective_chat.id
    comment = update.message.text
    requestID = context.user_data["REVIEW_REQUEST_INFO"]['requestID']
    role = context.user_data["REVIEW_REQUEST_INFO"]['role']
    rating = context.user_data["REVIEW_REQUEST_INFO"]['rating']
    prevMsgID = rating = context.user_data["REVIEW_REQUEST_INFO"]['prevMsgID']

    with DEAD_LOCK:
        with open('data/deadRequests.json', 'r') as file:
            deadRequestsDict = load(file)

        deadRequestsDict[requestID]['reviews'][role] = {'rating': rating, 'comments': comment}

        with open('data/deadRequests.json', 'w') as file:
            dump(deadRequestsDict, file, indent = 1)

    await context.bot.delete_message(chatID, prevMsgID)

    await context.bot.send_message(
        chatID,
        f"We have recorded your review for request *ID* \\#{requestID}\\.\
        \n\nThank you for your feedback\\.",
        parse_mode = "MarkdownV2",
        reply_markup = None
    )

    context.user_data.clear()

ReviewRequestCommentHandler = MessageHandler(
    filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
    ReviewRequestComment
)

ReviewRequestSTARTInlineHandler = CallbackQueryHandler(reviewRequest_START, pattern='^reviewRequestSTART')
ReviewRequestSELECTIONInlineHandler = CallbackQueryHandler(reviewRequest_SELECTION, pattern='^reviewRequestSELECTION')
ReviewRequestSAVESELECTIONInlineHandler = CallbackQueryHandler(reviewRequest_SAVE_SELECTION, pattern='^reviewRequestSAVESELECTION')
ReviewRequestOPENENDEDInlineHandler = CallbackQueryHandler(reviewRequest_SAVE_SELECTION, pattern='^reviewRequestOPENENDED')
