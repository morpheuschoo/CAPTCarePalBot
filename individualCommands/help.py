from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters
from ujson import load
from groupCommands.settings import Phase

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    with open('data/userDetails.json') as file:
        userDict = load(file)

    if str(chatID) not in userDict:
        await context.bot.send_message(chatID, "You have not registered, please use /start to register.")
        return

    if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT:
        await context.bot.send_message(chatID,
                                       f"We are now currently recruiting for volunteers\\!\
                                         \n\nUse /vr to sign up to be a volunteer\\.\
                                         \n\n_*Once you sign up, you do not need to do anything else\\.*_",
                                         parse_mode = 'MarkdownV2')
    else:
        userDetails = userDict.get(str(chatID))

        await context.bot.send_message(chatID,
                                       f"Need to make a request\\? Use /request to make one now\\!\
                                        \n\n*Requests made today: {userDetails['requestsMade']}* \
                                        \n\n_*Please note that you are only able to make up to 3 requests a day\\.*_",
                                       parse_mode = 'MarkdownV2')
        await context.bot.send_message(chatID, "If you notice any problems with me feel free to reach out to @jiexinn0220 or @morpheuschoo")

HelpHandler = CommandHandler("help", help, filters = filters.ChatType.PRIVATE)
