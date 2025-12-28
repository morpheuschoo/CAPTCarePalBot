from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    result = "NEED TO MAKE A REQUEST?\
              \n(medicine, food, etc.)\
              \n/request - to make a request\
              \n\nVOLUNTEER COMMANDS:\
              \n/vr - register as a volunteer\
              \n/vw - withdraw as a volunteer\
              \n\nADMIN COMMANDS:\
              \n/start - displays start message\
              \n/help - displays this message"

    await context.bot.send_message(chatID, result)

HelpHandler = CommandHandler("help", help)
