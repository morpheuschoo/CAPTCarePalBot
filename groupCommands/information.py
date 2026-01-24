from ujson import load
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram.ext import ContextTypes

from groupCommands.settings import Phase

async def runInformation(context: ContextTypes.DEFAULT_TYPE):
    with open('data/volunteerDetails.json') as file:
        volunteerList = load(file)

    with open('data/banList.json') as file:
        banList = load(file)

    with open('data/userDetails.json') as file:
        userDict = load(file)

    with open('data/pendingRequests.json') as file:
        pendingDict = load(file)

    with open('data/acceptedRequests.json') as file:
        acceptedDict = load(file)

    with open('data/deadRequests.json') as file:
        deadDict = load(file)

    with open('data/eosSurvey.json') as file:
        eosSurveyList = load(file)

    if not context.bot_data.get('EOSSURVEY_SENT_TIME'):
        text = f"\n\n*The EOS Survey has not been sent\\.*"
    else:
        text = f"\n\n*The EOS Survey was sent out at {context.bot_data['EOSSURVEY_SENT_TIME']}\\.*\
                 \n\n__EOS SURVEY__\
                 \nCompleted: {len(eosSurveyList)}"

    await context.bot.edit_message_text(
        chat_id = context.bot_data['ADMIN_GROUP_ID'],
        message_id = context.bot_data['INFORMATION_MESSAGE_ID'],
        text = f"*CAPT Care Pal is currently in the {'VOLUNTEER RECRUITMENT' if context.bot_data['PHASE'] == Phase.VOLUNTEER_RECRUITMENT else 'REQUEST'} phase\\.*\
                 \n\n__USER INFO__\
                 \nUsers: {len(userDict)}\
                 \nVolunteers: {len(volunteerList)}\
                 \nBanned: {len(banList)}\
                 \n\n__REQUESTS INFO__\
                 \nPending: {len(pendingDict)}\
                 \nAccepted: {len(acceptedDict)}\
                 \nDead: {len(deadDict)}"
                 + text +
                 f"\n\n_*Last updated: {datetime.now(ZoneInfo('Asia/Singapore')).strftime('%d %B %Y, %I:%M %p')}*_",
        parse_mode = 'MarkdownV2'
    )
