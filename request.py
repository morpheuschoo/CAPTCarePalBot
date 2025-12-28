from datetime import datetime
from ujson import load, dump
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

async def request_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    with open('data/userDetails.json') as file:
        userDict = load(file)

    if str(chatID) not in userDict:
        await context.bot.send_message(chatID, "You have not registered, please use /start to register.")
        return ConversationHandler.END

    keyboard = [['Buy medicine \U0001F48A'], ['Buy food \U0001F371'], ['Other requests']]

    await context.bot.send_message(chatID,
                                   f'What kind of help do you need?\n\nPlease choose from the options below.',
                                   reply_markup = ReplyKeyboardMarkup(keyboard))

    await context.bot.send_message(chatID, f'/cancel to cancel')

    return 1

async def request_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Buy medicine \U0001F48A' and input != 'Buy food \U0001F371' and input != 'Other requests':
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select "Buy medicine \U0001F48A", "Buy food \U0001F371", or "Other requests"')
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
                                       f'What food would you like?\
                                         \nPlease try to only put food available at Utown unless it is really needed.\
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
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select "Male preferred", "Female preferred", or "No preference"')
        return 3

    context.user_data['genderPreference'] = input

    keyboard = [['Yes, submit my request'], ['No, let me edit it again']]

    await context.bot.send_message(chatID,
                                   f'Great! Let me confirm your request:\
                                     \n\nType: {context.user_data['type']}\
                                     \nDetails: {context.user_data['details']}\
                                     \nGender Preference: {context.user_data['genderPreference']}\
                                     \n\nDoes this look correct?',
                                     reply_markup = ReplyKeyboardMarkup(keyboard))

    await context.bot.send_message(chatID, '/cancel to cancel')

    return 4

async def request_FIFTH(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Yes, submit my request' and input != 'No, let me edit it again':
        await context.bot.send_message(chatID, 'You have made an invalid selection. Please only select "Yes, submit my request" and "Female preferred", or "No, let me edit it again"')
        return 3

    if input == 'No, let me edit it again':
        keyboard = [['Buy medicine \U0001F48A'], ['Buy food \U0001F371'], ['Other requests']]
        await context.bot.send_message(chatID, f'What kind of help do you need?\n\nPlease choose from the options below.', reply_markup = ReplyKeyboardMarkup(keyboard))
        return 1

    await createRequest(chatID, context.user_data['type'], context.user_data['details'], context.user_data['genderPreference'])

    await context.bot.send_message(chatID, f'Your request has been submitted successfully!', reply_markup = ReplyKeyboardRemove())

    return ConversationHandler.END

async def createRequest(chatID, type, details, genderPreference):
    requestID = hex(int(datetime.now().timestamp()))[2:].upper()

    with open('data/volunteerDetails.json') as file:
        volunteerList = set(load(file))

    with open('data/userDetails.json') as file:
        userDict = load(file)

    validVolunteers = [volID for volID in volunteerList if str(volID) in userDict]

    if genderPreference == 'Male preferred':
        validVolunteers = [volID for volID in validVolunteers if userDict[str(volID)]['gender'] == 'Male']
    elif genderPreference == 'Female preferred':
        validVolunteers = [volID for volID in validVolunteers if userDict[str(volID)]['gender'] == 'Female']

    print(validVolunteers)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END


RequestHandler = ConversationHandler(
    entry_points = [CommandHandler('request', request_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_SECOND)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_THIRD)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_FOURTH)],
        4: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_FIFTH)],
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
