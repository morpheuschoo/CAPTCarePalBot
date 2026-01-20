from enum import Enum
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

class Phase(Enum):
    VOLUNTEER_RECRUITMENT = 0
    REQUEST_PHASE = 1

async def changePhase_FIRST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id

    if not chatID in context.bot_data['ADMINS']:
        await context.bot.send_message(chatID, 'You are not allowed to use this command.')
        return ConversationHandler.END

    await context.bot.send_message(chatID,
                                   f"The bot is currently in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.\
                                     \n\nType [YES] to change the bot to the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] != Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.")

    return 1

async def changePhase_SECOND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    input = update.message.text

    if input != 'YES':
        await context.bot.send_message(chatID,
                                       f"I did not receieve a [YES].\
                                         \n\nBot will remain in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.")
        return ConversationHandler.END

    context.bot_data['PHASE'] = Phase.REQUEST_PHASE if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else Phase.VOLUNTEER_RECRUITMENT
    await context.bot.send_message(chatID,
                                   f"The bot has been switched to the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    context.user_data.clear()
    await context.bot.send_message(chatID, "Goodbye!", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

ChangePhaseHandler = ConversationHandler(
    entry_points = [CommandHandler('phase', changePhase_FIRST)],
    states = {
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, changePhase_SECOND)]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
