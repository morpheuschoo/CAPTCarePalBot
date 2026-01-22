from ujson import load
from enum import Enum
from dotenv import load_dotenv
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

    if msg.text and msg.text in ["[CANCEL]", "[DONE, BROADCAST ALL]", "[DONE, BROADCAST VOLUNTEERS]"]:
        match msg.text:
            case "[CANCEL]":
                context.bot_data['BROADCAST_MESSAGES'] = []
                return
            case "[DONE, BROADCAST ALL]":
                context.bot_data['BROADCAST_TYPE'] = BroadcastType.BROADCAST_ALL
                await broadcast_confirm(update, context)
                context.bot_data['BROADCAST_MESSAGES'] = []
                return
            case "[DONE, BROADCAST VOLUNTEERS]":
                context.bot_data['BROADCAST_TYPE'] = BroadcastType.BROADCAST_VOLUNTEERS
                await broadcast_confirm(update, context)
                context.bot_data['BROADCAST_MESSAGES'] = []
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

async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for msg in context.bot_data['BROADCAST_MESSAGES']:
        match msg['type']:
            case MessageType.TEXT:
                await context.bot.send_message(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    text = msg['content']
                )
            case MessageType.PHOTO:
                await context.bot.send_photo(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    photo = msg['file_id'],
                    caption = msg['caption']
                )
            case MessageType.DOCUMENT:
                await context.bot.send_document(
                    chat_id = context.bot_data['ADMIN_GROUP_ID'],
                    message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
                    document = msg['file_id'],
                    caption = msg['caption']
                )

    keyboard = [[InlineKeyboardButton("Confirm", callback_data = "^confirmBroadcast$")],
                [InlineKeyboardButton("Cancel", callback_data = "^cancelBroadcast$")]]

    await context.bot.send_message(
        chat_id = context.bot_data['ADMIN_GROUP_ID'],
        message_thread_id = context.bot_data['BROADCAST_TOPIC_ID'],
        text = f"We will be broadcasting the above messages to *{'ALL' if context.bot_data['BROADCAST_TYPE'] == BroadcastType.BROADCAST_ALL else 'VOLUNTEERS'}*\\.\
                 \n\n_*Are you sure you would like to broadcast?*_",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def broadcast_messages(broadcastType: BroadcastType):
    sendList = []
    if broadcastType == BroadcastType.BROADCAST_ALL:
        with open('data/userDetails.json') as file:
            sendList = [int(x) for x in load(file).keys()]
    elif broadcastType == BroadcastType.BROADCAST_VOLUNTEERS:
        with open('data/volunteerDetails.json') as file:
            sendList = [int(x) for x in load(file)]

    print(sendList)

BroadcastHandler = MessageHandler(
    (filters.TEXT | filters.PHOTO | filters.Document.ALL)
        & ~filters.COMMAND
        & filters.ChatType.SUPERGROUP,
    broadcast
)
