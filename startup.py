import os
from ujson import dump
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder

from groupCommands.settings import Phase

async def startup(app: ApplicationBuilder):
    if not os.path.exists("data"):
        os.makedirs("data")

    list_files = ["volunteerDetails.json"]
    dict_files = ["userDetails.json", "pendingRequests.json", "acceptedRequests.json", "deadRequests.json"]

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

    app.bot_data['PHASE'] = Phase.REQUEST_PHASE

    load_dotenv()

    app.bot_data['ADMIN_GROUP_ID'] = int(os.getenv("ADMIN_GROUP_ID"))
    app.bot_data['SETTINGS_TOPIC_ID'] = int(os.getenv("SETTINGS_TOPIC_ID"))
    app.bot_data['BROADCAST_TOPIC_ID'] = int(os.getenv("BROADCAST_TOPIC_ID"))

    # Settings Topic
    keyboard = [[InlineKeyboardButton("Phase", callback_data = f'phase_ONE')]]

    await app.bot.send_message(
        chat_id = app.bot_data['ADMIN_GROUP_ID'],
        message_thread_id = app.bot_data['SETTINGS_TOPIC_ID'],
        text = f"*The bot is currently in the {'VOLUNTEER RECRUITMENT' if app.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*\
                  \n\nChoose one of the following settings:",
        parse_mode = "MarkdownV2",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

    # Broadcast Topic
    app.bot_data['BROADCAST_MESSAGES'] = []
    app.bot_data['BROADCAST_MESSAGE_DELETE_TRACKER'] = {'USER': [], 'BOT':[]}
    app.bot_data['BROADCAST_INTERMEDIATE'] = False
    app.bot_data['BROADCAST_TYPE'] = None

    msg = await app.bot.send_message(
        chat_id = app.bot_data['ADMIN_GROUP_ID'],
        message_thread_id = app.bot_data['BROADCAST_TOPIC_ID'],
        text = f"This is the broadcast channel\\. To use, type your message \\(in separate messages\\)\\. When you are done, type the command\\.\
                 \n\n__COMMANDS__\
                 \n*\\[DONE, BROADCAST ALL\\]* \\- done with message, broadcast to all users\
                 \n*\\[DONE, BROADCAST VOLUNTEERS\\]* \\- done with message, broadcast to all volunteers\
                 \n*\\[CANCEL\\]* \\- to retype message\
                 \n\n_*Only works for text \\(and emojis\\), documents \\(with captions\\) and photos \\(with captions\\)\\.*_",
        parse_mode = "MarkdownV2"
    )

    await app.bot.pin_chat_message(
        chat_id = app.bot_data['ADMIN_GROUP_ID'],
        message_id = msg.message_id,
        disable_notification = True
    )

    await app.bot.delete_message(
        chat_id = app.bot_data['ADMIN_GROUP_ID'],
        message_id = msg.message_id + 1
    )
