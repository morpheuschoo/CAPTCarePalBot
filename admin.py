from telegram import ReplyKeyboardRemove, Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from ujson import load

async def admin_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    if not chatID in context.bot_data['ADMINS']:
        await context.bot.send_message(chatID, 'You are not allowed to use this command.')
        return ConversationHandler.END

    with open('data/userDetails.json') as file:
        userDetailsDict = load(file)

    keyboard = []
    keyboardToChatIDMap = {}

    resultMsg = f"Select who you would like to make an admin.\n\nCURRENT ADMINS:"

    for chatID, details in userDetailsDict.items():
        if not int(chatID) in context.bot_data['ADMINS']:
            keyboard.append(details['fullName'])
            keyboardToChatIDMap[details['fullName']] = chatID
        else:
            print('fat')
            resultMsg += f"\n{details['fullName']}"

    context.user_data['map'] = keyboardToChatIDMap

    await context.bot.send_message(chatID, resultMsg, reply_markup = ReplyKeyboardMarkup(keyboard))
    await context.bot.send_message(chatID, f"/cancel to cancel")

    return 1

async def admin_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text
    map = context.user_data['map']

    if input not in map:
        await context.bot.send_message(chatID, "Please select a valid name.")
        return 1

    context.bot_data['ADMINS'].add(map[input])

    await context.bot.send_message(chatID, f'We have made {input} an adminstrator.')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    context.user_data.clear()
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

AdminHandler = ConversationHandler(
    entry_points = [CommandHandler('admin', admin_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_SECOND)]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
