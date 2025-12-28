from ujson import load, dump
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

async def start_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    with open('data/userDetails.json') as file:
        userDict = load(file)

    if str(chatID) in userDict:
        await context.bot.send_message(chatID, "You have already registered, use /help to see what you can do!")
        return ConversationHandler.END

    await context.bot.send_message(chatID,
                                   f"Hey there {update.message.chat.first_name}! \U0001F44B\
                                     \n\nWelcome to the CAPT Care Pal Bot!\
                                     \n\nInitiated by the Social Innovation (SI) Wing, this project aims to connect unwell CAPTains with volunteers within the CAPT community, and make support more readily available!\
                                     \n\nYou can submit a request, or join as a volunteer.")
    await context.bot.send_message(chatID,
                                   "=== PDPA ACKNOWLEDGEMENT ===\
                                    \n\nHowever, before we proceed, we need your consent!\
                                    \n\nBy using this service, you agree that the information you provide may be shared with volunteers and securely stored by CAPT for safety and service improvement.\
                                    \n\nDo you consent to these terms?", reply_markup = ReplyKeyboardMarkup([["Yes, I agree"], ["No, I do not agree"]]))
    return 1

async def start_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != "Yes, I agree":
        await context.bot.send_message(chatID, "No problem! If you change your mind, use /start again.", reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data['username'] = update.message.from_user.username

    await context.bot.send_message(chatID, "Thats great! Now we will register you into our system!", reply_markup = ReplyKeyboardRemove())
    await context.bot.send_message(chatID, "Please enter your full name below.")

    return 2

async def start_THIRD(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    context.user_data['fullName'] = ' '.join(update.message.text.split()).title()

    keyboard = [['Male'], ['Female'], ['Prefer not to say']]

    await context.bot.send_message(chatID,
                                   "Alright! Now we will need your gender (this is for matching preferences when making requests)",
                                   reply_markup = ReplyKeyboardMarkup(keyboard))

    return 3

async def start_FOURTH(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text.strip()

    if input != 'Male' and input != 'Female' and input != 'Prefer not to say':
        await context.bot.send_message(chatID, "You have made an invalid selection! Please select only Male, Female or Prefer not to say")
        return 3

    context.user_data['gender'] = input

    await context.bot.send_message(chatID, "Thank you for registering! We have recorded the following details down", reply_markup = ReplyKeyboardRemove())
    await context.bot.send_message(chatID,
                                   f"Full Name - {context.user_data['fullName']}\
                                     \nUsername - @{context.user_data['username']}\
                                     \nGender - {context.user_data['gender']}")
    await context.bot.send_message(chatID, "You can use /help to see what you can do!")

    with open('data/userDetails.json') as file:
        userDict = load(file)

    userDict[chatID] = {'username': context.user_data['username'],
                        'fullName': context.user_data['fullName'],
                        'gender': context.user_data['gender']}

    with open('data/userDetails.json', 'w') as file:
        dump(userDict, file, indent = 1)

    # TODO: Might want to add a way for them to edit their details

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

StartHandler = ConversationHandler(
    entry_points = [CommandHandler('start', start_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_SECOND)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_THIRD)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_FOURTH)],
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
