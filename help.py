from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from phase import Phase
from ujson import load

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    if chatID in context.bot_data['ADMINS']:
        with open('data/acceptedRequests.json') as file:
            acceptedRequestsDict = load(file)

        with open('data/deadRequests.json') as file:
            deadRequestsDict = load(file)

        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        with open('data/userDetails.json') as file:
            userDetailsDict = load(file)

        with open('data/volunteerDetails.json') as file:
            volunteerDetailsDict = load(file)

        await context.bot.send_message(chatID,
                                       f"===== ADMINSTRATOR HELP =====\
                                         \n\nCurrently the bot is in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.\
                                         \n\nregistered users: {len(userDetailsDict)}\
                                         \nvolunteers: {len(volunteerDetailsDict)}\
                                         \n\npending requests: {len(pendingRequestsDict)}\
                                         \naccepted requests: {len(acceptedRequestsDict)}\
                                         \ndead requests: {len(deadRequestsDict)}\
                                         \n\nADMIN COMMANDS:\
                                         \n/admin - make others of adminstrator status\
                                         \n/phase - change the phase\
                                         \n/broadcast - broadcast a message to all people\
                                         \n\nUSER COMMANDS:\
                                         \n/request - make a request\
                                         \n/vr - register as a volunteer (only in recruitment phase)")
        return

    if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT:
        await context.bot.send_message(chatID,
                                       f"We are now currently recruiting for volunteers\\!\
                                         \n\nUse /vr to sign up to be a volunteer\\.\
                                         \n\n_*Once you sign up, you do not need to do anything else\\.*_",
                                         parse_mode = 'MarkdownV2')
    else:

        with open('data/userDetails.json') as file:
            userDetails = load(file).get(str(chatID))

        await context.bot.send_message(chatID,
                                       f"Need to make a request\\? Use /request to make one now\\!\
                                        \n\n*Requests made today: {userDetails['requestsMade']}* \
                                        \n\n_*Please note that you are only able to make up to 3 requests a day\\.*_",
                                       parse_mode = 'MarkdownV2')
        await context.bot.send_message(chatID, "If you notice any problems with me feel free to reach out to @jiexinn0220 or @morpheuschoo")

HelpHandler = CommandHandler("help", help)
