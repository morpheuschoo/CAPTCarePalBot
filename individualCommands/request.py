from ujson import load, dump
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from individualCommands.requestManager import createRequest

async def request_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    with open('data/userDetails.json') as file:
        userDict = load(file)

    # Reject users who have not registered
    if str(chatID) not in userDict:
        await context.bot.send_message(chatID, "You have not registered, please use /start to register.")
        return ConversationHandler.END

    # Reject users who have already made 3 requests today
    if userDict.get(str(chatID))['requestsMade'] == 3:
        await context.bot.send_message(chatID, "You have already made 3 requests today. You will have to wait until tomorrow to make a new request.")
        return ConversationHandler.END

    with open('data/pendingRequests.json') as file:
        pendingRequestsDict = load(file)

    with open('data/acceptedRequests.json') as file:
        acceptedRequestsDict = load(file)

    # Reject users who have an active request
    if chatID in {request['requester'] for request in pendingRequestsDict.values()} | {request['requester'] for request in acceptedRequestsDict.values()}:
        await context.bot.send_message(chatID, "You have already sent a request, please wait until your request is fufilled or cancelled before sending another request.")
        return ConversationHandler.END

    keyboard = [['Buy medicine \U0001F48A'], ['Buy food \U0001F371'], ['Other requests']]

    await context.bot.send_message(chatID,
                                   f'You have made {userDict[str(chatID)]['requestsMade']} {"request" if userDict[str(chatID)]["requestsMade"] == 1 else "requests"} today.'
                                   + f' This will be your {["1st", "2nd", "3rd"][userDict[str(chatID)]['requestsMade']]} request for today.\
                                   \n\nWhat kind of help do you need?\n\nPlease choose from the options below.',
                                   reply_markup = ReplyKeyboardMarkup(keyboard))

    await context.bot.send_message(chatID, f'/cancel to cancel')

    return 1

async def request_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Buy medicine \U0001F48A' and input != 'Buy food \U0001F371' and input != 'Other requests':
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select [Buy medicine \U0001F48A], [Buy food \U0001F371], or [Other requests]')
        return 1

    context.user_data['type'] = input

    if input == 'Buy medicine \U0001F48A':
        await context.bot.send_message(chatID,
                                       f'What medicine do you need?\
                                         \n\nPlease provide details:\
                                         \n- Medicine/Supplement name (eg. paracetamol)\
                                         \n- Quantity (eg. 1 box, 10 tablets)\
                                         \n- Available location (if known, on or near campus)\
                                         \n- Any special instructions or notes (eg. dosage, allergies)\
                                         \n\nExample: "Panadol, 1 box, available at FairPrice@Utown"')

    elif input == 'Buy food \U0001F371':
        await context.bot.send_message(chatID,
                                       f'What food would you like? Please try to only put food available at Utown unless it is really needed.\
                                         \n\nPlease provide details:\
                                         \n- Food item (be specific)\
                                         \n- Preferred purchase location (eg. Flavours, Fine Foods)\
                                         \n- Preferred time range for delivery (eg, 12PM - 3PM)\
                                         \n- Quantity (eg. 1 meal)\
                                         \n- Any additional notes (allergies, budget, etc.)\
                                         \n\nExample: "Chicken rice, Flavours, 11AM - 2PM, 1 meal')

    else:
        await context.bot.send_message(chatID,
                                       f'Any special request you need?\
                                         \n\nPlease be as specific as possible:\
                                         \n- What is it?\
                                         \n- When do you need it?\
                                         \n- Any important details?\
                                         \n\nExample: "Accompaniment to UHC, preferred time: 2.30PM - 5PM"')

    await context.bot.send_message(chatID, '/cancel to cancel', reply_markup = ReplyKeyboardRemove())

    return 2

async def request_THIRD(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if len(input) > 100:
        await context.bot.send_message(chatID, 'Your request details are too long. Please keep it under 100 characters.')
        return 2

    context.user_data['details'] = input

    keyboard = [['Male preferred'], ['Female preferred'], ['No preference']]

    await context.bot.send_message(chatID,
                                   'Do you have a gender preference for the volunteer?\
                                    \n\nWe will only share your request with volunteers of gender you select. This helps ensure you are connected with someone you feel comfortable with.',
                                    reply_markup = ReplyKeyboardMarkup(keyboard))

    await context.bot.send_message(chatID, '/cancel to cancel')

    return 3

async def request_FOURTH(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Male preferred' and input != 'Female preferred' and input != 'No preference':
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select [Male preferred], [Female preferred], or [No preference]')
        return 3

    context.user_data['genderPreference'] = input

    keyboard = [['Yes, submit my request'], ['No, let me edit it again']]

    await context.bot.send_message(chatID,
                                   f'Great\\! Let me confirm your request\\.\
                                     \n\n__TYPE__\
                                     \n{context.user_data['type']}\
                                     \n\n__DETAILS__\
                                     \n{context.user_data['details']}\
                                     \n\n__GENDER PREFERENCE__\
                                     \n{context.user_data['genderPreference']}\
                                     \n\nDoes this look correct?',
                                     parse_mode = "MarkdownV2",
                                     reply_markup = ReplyKeyboardMarkup(keyboard))

    await context.bot.send_message(chatID, '/cancel to cancel')

    return 4

async def request_FIFTH(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Yes, submit my request' and input != 'No, let me edit it again':
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select [Yes, submit my request] or [No, let me edit it again]')
        return 4

    if input == 'No, let me edit it again':
        keyboard = [['Buy medicine \U0001F48A'], ['Buy food \U0001F371'], ['Other requests']]
        await context.bot.send_message(chatID, f'What kind of help do you need?\n\nPlease choose from the options below.', reply_markup = ReplyKeyboardMarkup(keyboard))
        return 1

    context.user_data['chatID'] = chatID

    # Record request
    with open('data/userDetails.json', 'r') as file:
        userDict = load(file)

    userDict[str(chatID)]['requestsMade'] += 1

    with open('data/userDetails.json', 'w') as file:
        dump(userDict, file, indent = 1)

    await createRequest(context)

    context.user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    context.user_data.clear()
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

RequestHandler = ConversationHandler(
    entry_points = [CommandHandler('request', request_FIRST, filters = filters.ChatType.PRIVATE)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, request_SECOND)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, request_THIRD)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, request_FOURTH)],
        4: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, request_FIFTH)],
    },
    fallbacks = [CommandHandler('cancel', cancel, filters = filters.ChatType.PRIVATE)]
)
