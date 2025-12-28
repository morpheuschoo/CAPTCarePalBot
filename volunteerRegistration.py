from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from ujson import load, dump

async def volunteerRegistration_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    username = update.message.from_user.username

    # Check if they have consented to PDPA
    with open('data/pdpa.json') as file:
        pdpaSet = set(load(file))

    if chatID not in pdpaSet:
        await context.bot.send_message(chatID, "You have not consented to PDPA, please use /start to consent.")
        return ConversationHandler.END

    # If they are already registered
    with open('data/volunteerDetails.json') as file:
        volunteerDict = load(file)

    if str(chatID) in volunteerDict:
        await context.bot.send_message(chatID, f"You are already registered as a volunteer with CAPT Care Pal!")
        return ConversationHandler.END

    context.user_data['username'] = username

    telegram_name = update.message.chat.first_name
    await context.bot.send_message(chatID,
                                   f'Is your name {telegram_name}?\n\nIf it is, type YES.\nIf it is not, type your name below.',
                                   reply_markup = ReplyKeyboardRemove())
    await context.bot.send_message(chatID, f'/cancel to exit')
    return 1

async def volunteerRegistration_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input == "YES":
        context.user_data['name'] = update.message.chat.first_name
    else:
        context.user_data['name'] = input

    keyboard = [['MALE'], ['FEMALE'], ['PREFER NOT TO SAY']]

    await context.bot.send_message(chatID, f"Thanks {context.user_data['name']}! We would like to know you gender!",
                                   reply_markup = ReplyKeyboardMarkup(keyboard))
    await context.bot.send_message(chatID, f'/cancel to exit')
    return 2

async def volunteerRegistration_THIRD(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input == "MALE" or input == "FEMALE":
        context.user_data['gender'] = input
    elif input == "PREFER NOT TO SAY":
        context.user_data['gender'] = None
    else:
        await context.bot.send_message(chatID, f'Invalid input please only type MALE, FEMALE or PREFER NOT TO SAY')
        await context.bot.send_message(chatID, f'/cancel to exit')
        return 3

    with open('data/volunteerDetails.json') as file:
        volunteerDict = load(file)

    volunteerDict[chatID] = {'username': context.user_data['username'],
                             'name': context.user_data['name'],
                             'gender': context.user_data['gender']}

    with open('data/volunteerDetails.json', 'w') as file:
        dump(volunteerDict, file, indent = 1)

    await context.bot.send_message(chatID,
                                   f'Thank you for registering as a volunteer. We have recordeded these details:\
                                    \n\nusername - {context.user_data['username']}\
                                    \nname - {context.user_data['name']} \
                                    \ngender - {context.user_data['gender']}',
                                    reply_markup = ReplyKeyboardRemove())

    # TODO: EDIT PARTICULARS
    await context.bot.send_message(chatID, f'If you would like to edit your particulars, use the command /...')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

VolunteerRegistrationHandler = ConversationHandler(
    entry_points = [CommandHandler('vr', volunteerRegistration_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, volunteerRegistration_SECOND)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, volunteerRegistration_THIRD)]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
