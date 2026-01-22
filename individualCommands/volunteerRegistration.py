from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from ujson import load, dump
from groupCommands.settings import Phase

async def volunteerRegistration_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    if context.bot_data['PHASE'] != Phase.VOLUNTEER_RECRUITMENT:
        await context.bot.send_message(chatID, "Sorry, the volunteer recruitment period has ended.")
        return ConversationHandler.END

    # Check if they have registered
    with open('data/userDetails.json') as file:
        userDict = load(file)

    if str(chatID) not in userDict:
        await context.bot.send_message(chatID, "You have not registered, please use /start to register.")
        return ConversationHandler.END

    # If they have already registered as a volunteer
    with open('data/volunteerDetails.json') as file:
        volunteerSet = set(load(file))

    if chatID in volunteerSet:
        await context.bot.send_message(chatID, f"You are already registered as a volunteer with CAPT Care Pal!")
        return ConversationHandler.END

    await context.bot.send_message(chatID,
                                   f'You will be registering as a volunteer with CAPT Care Pal.\
                                     TODO ... Terms and Conditions')
    await context.bot.send_message(chatID, f'Do you agree to be a volunteer?', reply_markup = ReplyKeyboardMarkup([['Yes, I agree'], ['No, I do not agree']]))

    return 1

async def volunteerRegistration_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Yes, I agree':
        await context.bot.send_message(chatID, f'No problem! If you would like up sign up to be a volunteer, you can use /vr again.', reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END

    with open('data/userDetails.json') as file:
        userDict = load(file)

    with open('data/volunteerDetails.json') as file:
        volunteerSet = set(load(file))

    volunteerSet.add(chatID)

    with open('data/volunteerDetails.json', 'w') as file:
        dump(list(volunteerSet), file, indent = 1)

    await context.bot.send_message(chatID, f'Thank you {userDict[str(chatID)]['fullName']}! We have signed you up as a volunteer.', reply_markup = ReplyKeyboardRemove())

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

VolunteerRegistrationHandler = ConversationHandler(
    entry_points = [CommandHandler('vr', volunteerRegistration_FIRST, filters = filters.ChatType.PRIVATE)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, volunteerRegistration_SECOND)]
    },
    fallbacks = [CommandHandler('cancel', cancel, filters = filters.ChatType.PRIVATE)]
)
