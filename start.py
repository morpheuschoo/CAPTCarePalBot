from ujson import load, dump
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

async def start_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    with open('data/pdpa.json') as file:
        pdpaList = load(file)

    pdpaSet = set(pdpaList)

    if chatID in pdpaSet:
        await context.bot.send_message(chatID, "You have already consented to PDPA, use /help to find out more.")
        return ConversationHandler.END


    await context.bot.send_message(chatID,
                                   "Hey there! \U0001F44B\
                                    \n\nWelcome to the CAPT Care Pal Bot!\
                                    \n\nInitiated by the Social Innovation (SI) Wing, this project aims to connect unwell CAPTains with volunteers within the CAPT community, and make support more readily available!\
                                    \n\nYou can submit a request, or join as a volunteer.")
    await context.bot.send_message(chatID,
                                   "=== PDPA ACKNOWLEDGEMENT ===\
                                    \n\nHowever, before we proceed, we need your consent!\
                                    \n\nBy using this service, you agree that the information you provide may be shared with volunteers and securely stored by CAPT for safety and service improvement.\
                                    \n\nDo you consent to these terms?", reply_markup = ReplyKeyboardMarkup([["YES"], ["NO"]]))
    return 1

async def start_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != "YES":
        await context.bot.send_message(chatID, "No problem! If you change your mind, use /start again", reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END

    with open('data/pdpa.json') as file:
        pdpaList = load(file)

    pdpaSet = set(pdpaList)

    pdpaSet.add(chatID)

    with open('data/pdpa.json', 'w') as file:
        dump(list(pdpaSet), file, indent = 1)

    await context.bot.send_message(chatID, "Thats great! Use /help to get started!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

StartHandler = ConversationHandler(
    entry_points = [CommandHandler('start', start_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_SECOND)],
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
