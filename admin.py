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

    resultMsg = f"Select an admin from USERS.\n\nUSERS (NON-ADMIN):"

    adminsStr = "\n\nADMINS:"

    for id, details in userDetailsDict.items():
        id = int(id)
        if not id in context.bot_data['ADMINS']:
            nameAndHandle = f"{details['fullName']} (@{details['username']})"
            keyboard.append([nameAndHandle])
            keyboardToChatIDMap[nameAndHandle] = id
            resultMsg += "\n" + nameAndHandle
        else:
            adminsStr += f"\n{details['fullName']} (@{details['username']})"

    resultMsg += adminsStr

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

    context.user_data.clear()

    await context.bot.send_message(chatID, f'We have made {input} an adminstrator.', reply_markup = ReplyKeyboardRemove())

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
