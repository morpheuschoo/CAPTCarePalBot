from enum import Enum
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from ujson import load, dump
from telegram.ext import ContextTypes, CallbackQueryHandler
from filelock import FileLock

PENDING_LOCK = FileLock("data/pendingRequests.json.lock")
ACCEPTED_LOCK = FileLock("data/acceptedRequests.json.lock")
DEAD_LOCK = FileLock("data/deadRequests.json.lock")
USER_LOCK = FileLock("data/userDetails.json.lock")
VOLUNTEER_LOCK = FileLock("data/volunteerDetails.json.lock")

async def createRequest(context: ContextTypes.DEFAULT_TYPE):
    requestID = uuid4().hex[:12].upper()

    with open('data/volunteerDetails.json') as file:
        volunteerSet = set(load(file))

    with open('data/userDetails.json') as file:
        userDict = load(file)

    if context.user_data['genderPreference'] == 'Male preferred':
        validVolunteers = {volID for volID in volunteerSet if volID != context.user_data['chatID'] and userDict[str(volID)]['gender'] == 'Male'}
    elif context.user_data['genderPreference'] == 'Female preferred':
        validVolunteers = {volID for volID in volunteerSet if volID != context.user_data['chatID'] and userDict[str(volID)]['gender'] == 'Female'}
    else:
        validVolunteers = volunteerSet - {context.user_data['chatID']}

    payload = {
        'requester': context.user_data['chatID'],
        'acceptor': None,
        'type': context.user_data['type'],
        'details': context.user_data['details'],
        'createdAt': datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
        'acceptedAt': None,
        'completedAt': None,
        'cancelledAt': None,
        'expiredAt': None,
        'completedBy': [],
        'chatIDToMsgIDMap': {},
        'decliners': {},
        'reviews': {'requester': {}, 'acceptor': {}},
        'status': 'pending'
    }

    keyboard = [[InlineKeyboardButton("Cancel Request", callback_data = f'cancelRequest_{requestID}')]]

    await context.bot.send_message(context.user_data['chatID'], 'Thank you for using CAPT Care Pal Bot!', reply_markup = ReplyKeyboardRemove())

    msg = await context.bot.send_message(context.user_data['chatID'],
                                         f'We have submitted your request\\!\
                                           \n\n*ID:* \\#{requestID}\
                                           \n\nWhat happens now:\
                                           \n\n1\\. Your request has already been forwarded to the volunteers\\.\
                                           \n\n2\\. If a volunteer accepts, we will share your name and Telegram contact with them and provide you with the volunteer\'s name and Telegram context so you can coordinate directly\\.\
                                           \n\n2\\. If no volunteer accepts within 30 minutes, we will notify you\\.\
                                           \n\n4\\. You can cancel the request anytime if you no longer need assistance\\.\
                                           \n\n_*Note that requests will expire automatically if not accepted within 24 hours\\.*_',
                                         parse_mode = 'MarkdownV2',
                                         reply_markup = InlineKeyboardMarkup(keyboard))

    payload['chatIDToMsgIDMap'][context.user_data['chatID']] = msg.message_id

    keyboard = [[InlineKeyboardButton("Accept Request", callback_data = f'acceptRequest_{requestID}'),
                 InlineKeyboardButton("Decline Request", callback_data = f'declineRequest_{requestID}')]]

    # send request to all available volunteers
    for sendeeID in list(validVolunteers):
        msg = await context.bot.send_message(sendeeID,
                                             f'\\=\\=\\=\\=\\= NEW REQUEST \\=\\=\\=\\=\\=\
                                               \n\n*ID:* \\#{requestID}\
                                               \n\n*Created at:* {datetime.fromisoformat(payload['createdAt']).strftime('%d %B %Y, %I:%M %p')}\
                                               \n\n{payload['type']}\
                                               \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                               \n{payload['details']}\
                                               \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-',
                                             parse_mode = 'MarkdownV2',
                                             reply_markup = InlineKeyboardMarkup(keyboard))

        payload['chatIDToMsgIDMap'][sendeeID] = msg.message_id

    # TODO: CHANGE TIMING TO 15 MINUTES (CURRENTLY FOR TESTING)
    context.job_queue.run_once(
        callback = fifteenMinutesRequestMessage,
        when = 10,
        data = {'requestID': requestID},
        name = requestID
    )

    with PENDING_LOCK:
        with open('data/pendingRequests.json') as file:
            requestsDict = load(file)

        requestsDict[requestID] = payload

        with open('data/pendingRequests.json', 'w') as file:
            dump(requestsDict, file, indent = 1)

async def cancelRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    requestID = query.data.split('_')[-1]

    for job in context.job_queue.get_jobs_by_name(requestID):
        job.schedule_removal()

    with PENDING_LOCK, DEAD_LOCK:
        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        with open('data/deadRequests.json') as file:
            deadRequestsDict = load(file)

        payload = pendingRequestsDict.get(requestID)
        payload['cancelledAt'] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        payload['status'] = 'cancelled'

        deadRequestsDict[requestID] = payload
        del pendingRequestsDict[requestID]

        with open('data/pendingRequests.json', 'w') as file:
            dump(pendingRequestsDict, file, indent = 1)

        with open('data/deadRequests.json', 'w') as file:
            dump(deadRequestsDict, file, indent = 1)

    for chatID, msgID in payload['chatIDToMsgIDMap'].items():
        if payload['requester'] == int(chatID):
            await context.bot.edit_message_text(f"You have cancelled your request\\!\
                                                  \n\n*ID:* \\#{requestID}\
                                                  \n\n*Cancelled at:* {datetime.fromisoformat(payload['cancelledAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                  \n\n_*You may now create another request\\.*_",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)
        else:
            await context.bot.edit_message_text(f"\\=\\=\\=\\=\\= REQUEST CANCELLED \\=\\=\\=\\=\\=\
                                                \n\n*ID:* \\#{requestID}\
                                                \n\n*Cancelled at:* {datetime.fromisoformat(payload['cancelledAt']).strftime('%d %B %Y, %I:%M %p')}",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)

async def acceptRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    requestID = query.data.split('_')[-1]

    for job in context.job_queue.get_jobs_by_name(requestID):
        job.schedule_removal()

    with PENDING_LOCK, USER_LOCK:
        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        payload = pendingRequestsDict.get(requestID)

        with open('data/userDetails.json') as file:
            userDict = load(file)

    payload['acceptor'] = query.from_user.id
    payload['acceptedAt'] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
    payload['status'] = 'accepted'

    keyboard = [[InlineKeyboardButton("Complete Request", callback_data = f'completeRequest_{requestID}')]]

    for chatID, msgID in payload['chatIDToMsgIDMap'].items():
        if payload['requester'] == int(chatID):
            await context.bot.edit_message_text(f"Your request has been accepted\\! We will be sending the details in a new message\\.\
                                                \n\n*ID:* \\#{requestID}\
                                                \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)

            msg = await context.bot.send_message(chatID,
                                                 f"Good news\\! A volunteer has accepted your request\\!\
                                                 \n\n*ID:* \\#{requestID}\
                                                 \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                 \n\nVolunteer name: {userDict[str(payload['acceptor'])]['fullName']}\
                                                 \nVolunteer contact: @{userDict[str(payload['acceptor'])]['username']}\
                                                 \n\n\\=\\=\\=\\=\\= REQUEST \\=\\=\\=\\=\\=\
                                                 \n\n{payload['type']}\
                                                 \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                                 \n{payload['details']}\
                                                 \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-",
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = InlineKeyboardMarkup(keyboard))

            payload['chatIDToMsgIDMap'][chatID] = msg.message_id

        else:
            await context.bot.edit_message_text(f"\\=\\=\\=\\=\\= REQUEST ACCEPTED \\=\\=\\=\\=\\=\
                                                \n\n*ID:* \\#{requestID}\
                                                \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)

            if payload['acceptor'] == int(chatID):
                msg = await context.bot.send_message(chatID,
                                                     f"Thank you for accepting a request\\!\
                                                     \n\n*ID:* \\#{requestID}\
                                                     \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                     \n\nRecepient name: {userDict[str(payload['requester'])]['fullName']}\
                                                     \nRecepient contact: @{userDict[str(payload['requester'])]['username']}\
                                                     \n\n\\=\\=\\=\\=\\= REQUEST \\=\\=\\=\\=\\=\
                                                     \n\n{payload['type']}\
                                                     \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                                     \n{payload['details']}\
                                                     \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-",
                                                    parse_mode = 'MarkdownV2',
                                                    reply_markup = InlineKeyboardMarkup(keyboard))

                payload['chatIDToMsgIDMap'][chatID] = msg.message_id

    with PENDING_LOCK, ACCEPTED_LOCK:
        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        if requestID not in pendingRequestsDict or pendingRequestsDict[requestID].get('status') != 'pending':
            await query.answer("Request was cancelled/accepted by somebody else", show_alert=True)
            return

        with open('data/acceptedRequests.json') as file:
            acceptedRequestsDict = load(file)

        acceptedRequestsDict[requestID] = payload
        del pendingRequestsDict[requestID]

        with open('data/pendingRequests.json', 'w') as file:
            dump(pendingRequestsDict, file, indent = 1)

        with open('data/acceptedRequests.json', 'w') as file:
            dump(acceptedRequestsDict, file, indent = 1)


async def declineRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    requestID = query.data.split('_')[-1]

    with PENDING_LOCK:
        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        payload = pendingRequestsDict.get(requestID)
        msgID = payload['chatIDToMsgIDMap'].pop(str(query.from_user.id), None)
        payload['decliners'][query.from_user.id] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()

        with open('data/pendingRequests.json', 'w') as file:
            dump(pendingRequestsDict, file, indent = 1)

    await context.bot.edit_message_text(f"\\=\\=\\=\\=\\= REQUEST DECLINED \\=\\=\\=\\=\\=\
                                          \n\n*ID:* \\#{requestID}\
                                          \n\n*Declined at:* {datetime.fromisoformat(payload['decliners'][query.from_user.id]).strftime('%d %B %Y, %I:%M %p')}",
                                        query.from_user.id,
                                        msgID,
                                        parse_mode = 'MarkdownV2',
                                        reply_markup = None)

async def completeRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    requestID = query.data.split('_')[-1]

    with ACCEPTED_LOCK, USER_LOCK:
        with open('data/userDetails.json') as file:
            userDict = load(file)

        with open('data/acceptedRequests.json') as file:
            payload = load(file).get(requestID)

    if query.from_user.id in payload['completedBy']:
        return

    payload['completedBy'].append(query.from_user.id)

    if payload['requester'] in payload['completedBy'] and payload['acceptor'] in payload['completedBy']:
        payload['completedAt'] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        payload['status'] = 'completed'

        with ACCEPTED_LOCK, DEAD_LOCK:
            with open('data/acceptedRequests.json') as file:
                acceptedRequestsDict = load(file)

            with open('data/deadRequests.json') as file:
                deadRequestsDict = load(file)

            deadRequestsDict[requestID] = payload
            del acceptedRequestsDict[requestID]

            with open('data/acceptedRequests.json', 'w') as file:
                dump(acceptedRequestsDict, file, indent = 1)

            with open('data/deadRequests.json', 'w') as file:
                dump(deadRequestsDict, file, indent = 1)

        await context.bot.edit_message_text(f'\\=\\=\\=\\=\\= REQUEST COMPLETED \\=\\=\\=\\=\\=\
                                              \n\n*ID:* \\#{requestID}\
                                              \n\n*Completed on:* {datetime.fromisoformat(payload['completedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                              \n\n{payload['type']}\
                                              \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                              \n{payload['details']}\
                                              \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                              \n\n_*You may now make another request\\.*_',
                                            payload['requester'],
                                            payload['chatIDToMsgIDMap'][str(payload['requester'])],
                                            parse_mode = 'MarkdownV2',
                                            reply_markup = [InlineKeyboardButton("Leave a review", callback_data = f'reviewRequestSTART_requester_{requestID}')])

        await context.bot.edit_message_text(f'\\=\\=\\=\\=\\= REQUEST COMPLETED \\=\\=\\=\\=\\=\
                                              \n\n*ID:* \\#{requestID}\
                                              \n\n*Completed on:* {datetime.fromisoformat(payload['completedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                              \n\n{payload['type']}\
                                              \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                              \n{payload['details']}\
                                              \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                              \n\n_*Thank you for fulfilling {userDict[str(payload['requester'])]['fullName']}\'s request\\!*_',
                                            payload['acceptor'],
                                            payload['chatIDToMsgIDMap'][str(payload['acceptor'])],
                                            parse_mode = 'MarkdownV2',
                                            reply_markup = [InlineKeyboardButton("Leave a review", callback_data = f'reviewRequestSTART_acceptor_{requestID}')])
    else:
        with ACCEPTED_LOCK:
            with open('data/acceptedRequests.json') as file:
                acceptedRequestsDict = load(file)

            acceptedRequestsDict[requestID] = payload

            with open('data/acceptedRequests.json', 'w') as file:
                dump(acceptedRequestsDict, file, indent = 1)

        with open('data/userDetails.json') as file:
            userDict = load(file)

        if query.from_user.id == payload['requester']:
            await context.bot.edit_message_text(f"You have marked this request as completed\\!\
                                                  \n\n_*We are waiting for {userDict[str(payload['acceptor'])]['fullName']} to mark this request as complete\\.\\.\\.*_\
                                                  \n\n*ID:* \\#{requestID}\
                                                  \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                  \n\nVolunteer name: {userDict[str(payload['acceptor'])]['fullName']}\
                                                  \nVolunteer contact: @{userDict[str(payload['acceptor'])]['username']}\
                                                  \n\n\\=\\=\\=\\=\\= REQUEST \\=\\=\\=\\=\\=\
                                                  \n\n{payload['type']}\
                                                  \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                                  \n{payload['details']}\
                                                  \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-",
                                                payload['requester'],
                                                payload['chatIDToMsgIDMap'][str(payload['requester'])],
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)
        else:
            await context.bot.edit_message_text(f"Thank you for fulfilling this reqeust\\!\
                                                  \n\n_*We are waiting for {userDict[str(payload['requester'])]['fullName']} to mark this request as complete\\.\\.\\.*_\
                                                  \n\n*ID:* \\#{requestID}\
                                                  \n\n*Accepted at:* {datetime.fromisoformat(payload['acceptedAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                  \n\nRecepient name: {userDict[str(payload['requester'])]['fullName']}\
                                                  \nRecepient contact: @{userDict[str(payload['requester'])]['username']}\
                                                  \n\n\\=\\=\\=\\=\\= REQUEST \\=\\=\\=\\=\\=\
                                                  \n\n{payload['type']}\
                                                  \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                                  \n{payload['details']}\
                                                  \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-",
                                                payload['acceptor'],
                                                payload['chatIDToMsgIDMap'][str(payload['acceptor'])],
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)

async def fifteenMinutesRequestMessage(context: ContextTypes.DEFAULT_TYPE):
    requestID = context.job.data['requestID']

    with PENDING_LOCK:
        with open('data/pendingRequests.json') as file:
            payload = load(file).get(requestID)

        keyboard = [[InlineKeyboardButton("Accept Request", callback_data = f'acceptRequest_{requestID}'),
                    InlineKeyboardButton("Decline Request", callback_data = f'declineRequest_{requestID}')]]

        for chatID, msgID in payload['chatIDToMsgIDMap'].items():
            if int(chatID) == payload['requester']:
                continue

            await context.bot.delete_message(chatID, msgID)
            msg = await context.bot.send_message(chatID,
                                                f'\\=\\=\\=\\=\\= PENDING REQUEST \\=\\=\\=\\=\\=\
                                                \n\n*ID:* \\#{requestID}\
                                                \n\n*Created at:* {datetime.fromisoformat(payload['createdAt']).strftime('%d %B %Y, %I:%M %p')}\
                                                \n\n{payload['type']}\
                                                \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\
                                                \n{payload['details']}\
                                                \n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-',
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = InlineKeyboardMarkup(keyboard))

            payload['chatIDToMsgIDMap'][chatID] = msg.message_id

        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        pendingRequestsDict[requestID] = payload

        with open('data/pendingRequests.json', 'w') as file:
            dump(pendingRequestsDict, file, indent = 1)

    # TODO: CHANGE TIMING TO 15 MINUTES (CURRENTLY FOR TESTING)
    context.job_queue.run_once(
        callback = thirtyMinutesRequestMessage,
        when = 10,
        data = {'requestID': requestID},
        name = requestID
    )

async def thirtyMinutesRequestMessage(context: ContextTypes.DEFAULT_TYPE):
    requestID = context.job.data['requestID']

    with open('data/pendingRequests.json') as file:
        payload = load(file).get(requestID)

    await context.bot.send_message(payload['requester'],
                                   f"We're sorry \U0001F614\
                                     \n\n*ID:* \\#{requestID}\
                                     \n\nNo one was available to help with your request in 30 minutes\\.\
                                     \n\nWe will leave your request up for another 24 hours before it expires\\.\
                                     \n\n_*You can still cancel your request by clicking on the \\[Cancel Request\\] button situated below the confirmation message\\.*_",
                                     parse_mode = "MarkdownV2")

    # TODO: CHANGE TIMING TO 24 HOURS (CURRENTLY FOR TESTING)
    context.job_queue.run_once(
        callback = expiredRequest,
        when = 10,
        data = {'requestID': requestID},
        name = requestID
    )

async def expiredRequest(context: ContextTypes.DEFAULT_TYPE):
    requestID = context.job.data['requestID']

    with PENDING_LOCK, DEAD_LOCK:
        with open('data/pendingRequests.json') as file:
            pendingRequestsDict = load(file)

        with open('data/deadRequests.json') as file:
            deadRequestsDict = load(file)

        payload = pendingRequestsDict.get(requestID)
        payload['expiredAt'] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        payload['status'] = 'expired'

        deadRequestsDict[requestID] = payload
        del pendingRequestsDict[requestID]

        with open('data/pendingRequests.json', 'w') as file:
            dump(pendingRequestsDict, file, indent = 1)

        with open('data/deadRequests.json', 'w') as file:
            dump(deadRequestsDict, file, indent = 1)

    for chatID, msgID in payload['chatIDToMsgIDMap'].items():
        if payload['requester'] == int(chatID):
            await context.bot.edit_message_text(f"Your request has expired\\!\
                                                  \n\n*ID:* \\#{requestID}\
                                                  \n\n*Expired on:* {datetime.fromisoformat(payload['expiredAt']).strftime('%d %B %Y, %I:%M %p')}",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)
            await context.bot.send_message(chatID,
                                           f"Please note that your request has expired\\.\
                                             \n\n*ID:* \\#{requestID}\
                                             \n\n*Expired on:* {datetime.fromisoformat(payload['expiredAt']).strftime('%d %B %Y, %I:%M %p')}\
                                             \n\n_*You may now create another request\\.*_",
                                             parse_mode = 'MarkdownV2')
        else:
            await context.bot.edit_message_text(f"\\=\\=\\=\\=\\= REQUEST EXPIRED \\=\\=\\=\\=\\=\
                                                  \n\n*ID:* \\#{requestID}\
                                                  \n\n*Expired on:* {datetime.fromisoformat(payload['expiredAt']).strftime('%d %B %Y, %I:%M %p')}",
                                                chatID,
                                                msgID,
                                                parse_mode = 'MarkdownV2',
                                                reply_markup = None)

CancelRequestInlineHandler = CallbackQueryHandler(cancelRequest, pattern='^cancelRequest')
AcceptRequestInlineHandler = CallbackQueryHandler(acceptRequest, pattern='^acceptRequest')
DeclineRequestInlineHandler = CallbackQueryHandler(declineRequest, pattern='^declineRequest')
CompleteRequestInlineHandler = CallbackQueryHandler(completeRequest, pattern='^completeRequest')
