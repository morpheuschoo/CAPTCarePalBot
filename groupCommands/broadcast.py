from ujson import load
from enum import Enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, filters, CallbackQueryHandler, MessageHandler

class BroadcastType(Enum):
    BROADCAST_ALL = 0
    BROADCAST_VOLUNTEERS = 1

class MessageType(Enum):
    TEXT = 0
    DOCUMENT = 1
    PHOTO = 2

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if context.bot_data['BROADCAST_INTERMEDIATE']:
        await msg.delete()
        return

    context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER']['USER'].append(msg.id)

    if msg.text and msg.text in ["[CANCEL]", "[DONE, BROADCAST ALL]", "[DONE, BROADCAST VOLUNTEERS]"]:
        match msg.text:
            case "[CANCEL]":
                context.bot_data['BROADCAST_MESSAGES'] = []
                return
            case "[DONE, BROADCAST ALL]":
                context.bot_data['BROADCAST_TYPE'] = BroadcastType.BROADCAST_ALL
                await broadcastIntermediate(update, context)
                return
            case "[DONE, BROADCAST VOLUNTEERS]":
                context.bot_data['BROADCAST_TYPE'] = BroadcastType.BROADCAST_VOLUNTEERS
                await broadcastIntermediate(update, context)
                return

    payload = {}

    if msg.text:
        payload = {
            'type': MessageType.TEXT,
            'content': msg.text
        }
    elif msg.photo:
        payload = {
            'type': MessageType.PHOTO,
            'file_id': msg.photo[-1].file_id,
            'caption': msg.caption or ''
        }
    elif msg.document:
        payload = {
            'type': MessageType.DOCUMENT,
            'file_id': msg.document.file_id,
            'caption': msg.caption or ''
        }

    if payload:
        context.bot_data['BROADCAST_MESSAGES'].append(payload)

async def broadcastIntermediate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sentMsg = None
    for msg in context.bot_data['BROADCAST_MESSAGES']:
        match msg['type']:
            case MessageType.TEXT:
                sentMsg = await context.bot.send_message(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    text = msg['content']
                )
            case MessageType.PHOTO:
                sentMsg = await context.bot.send_photo(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    photo = msg['file_id'],
                    caption = msg['caption']
                )
            case MessageType.DOCUMENT:
                sentMsg = await context.bot.send_document(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    document = msg['file_id'],
                    caption = msg['caption']
                )

        context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER']['BOT'].append(sentMsg.message_id)

    context.bot_data['BROADCAST_INTERMEDIATE'] = True

    keyboard = [[InlineKeyboardButton("Confirm", callback_data = "confirmBroadcast")],
                [InlineKeyboardButton("Cancel", callback_data = "cancelBroadcast")]]

    await context.bot.send_message(
        chat_id = context.bot_data['ADMIN_GROUP_ID'],
        message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
        text = f"We will be broadcasting the above messages to *{'ALL' if context.bot_data['BROADCAST_TYPE'] == BroadcastType.BROADCAST_ALL else 'VOLUNTEERS'}*\
                 \n\n_*Are you sure you would like to broadcast?*_",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def confirmBroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    for msgID in context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER']['USER']:
        await context.bot.delete_message(
            chat_id = context.bot_data['ADMIN_GROUP_ID'],
            message_id = msgID
        )

    await query.edit_message_text(
        f"Messages above has been broadcasted to *{'ALL' if context.bot_data['BROADCAST_TYPE'] == BroadcastType.BROADCAST_ALL else 'VOLUNTEERS'}*\
          \n\nBroadcasted by {'@' + query.from_user.username if query.from_user.username else '[NO USERNAME]'}",
          parse_mode = "MarkdownV2",
          reply_markup = None
    )

    sendList = []
    if context.bot_data['BROADCAST_TYPE'] == BroadcastType.BROADCAST_ALL:
        with open('data/userDetails.json') as file:
            sendList = [int(x) for x in load(file).keys()]
    elif context.bot_data['BROADCAST_TYPE'] == BroadcastType.BROADCAST_VOLUNTEERS:
        with open('data/volunteerDetails.json') as file:
            sendList = [int(x) for x in load(file)]

    for chatID in sendList:
        for msg in context.bot_data['BROADCAST_MESSAGES']:
            match msg['type']:
                case MessageType.TEXT:
                    await context.bot.send_message(
                        chat_id = chatID,
                        text = msg['content']
                    )
                case MessageType.PHOTO:
                    await context.bot.send_photo(
                        chat_id = chatID,
                        photo = msg['file_id'],
                        caption = msg['caption']
                    )
                case MessageType.DOCUMENT:
                    await context.bot.send_document(
                        chat_id = chatID,
                        document = msg['file_id'],
                        caption = msg['caption']
                    )

    context.bot_data['BROADCAST_INTERMEDIATE'] = False
    context.bot_data['BROADCAST_TYPE'] = None
    context.bot_data['BROADCAST_MESSAGES'] = []
    context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER'] = {'USER': [], 'BOT':[]}

async def cancelBroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.delete_message()

    for msgID in context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER']['USER'] + context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER']['BOT']:
        await context.bot.delete_message(
            chat_id = context.bot_data['ADMIN_GROUP_ID'],
            message_id = msgID
        )

    context.bot_data['BROADCAST_INTERMEDIATE'] = False
    context.bot_data['BROADCAST_TYPE'] = None
    context.bot_data['BROADCAST_MESSAGES'] = []
    context.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER'] = {'USER': [], 'BOT':[]}

BroadcastHandler = MessageHandler(
    (filters.TEXT | filters.PHOTO | filters.Document.ALL)
        & ~filters.COMMAND
        & filters.ChatType.SUPERGROUP,
    broadcast
)

ConfirmBroadcastInlineHandler = CallbackQueryHandler(confirmBroadcast, pattern='^confirmBroadcast$')
CancelBroadcastInlineHandler = CallbackQueryHandler(cancelBroadcast, pattern='^cancelBroadcast$')
