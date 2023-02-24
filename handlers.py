import os
import json
import uuid
import boto3
import datetime
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, constants
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from classes import UserObject, ReminderObject
from filter import match_date

# Stages + Callback data
USER_ROUTE, REMINDER_ROUTE, EDIT_REMINDER_ROUTE, SETTINGS_ROUTE, TYPE_SETTINGS_ROUTE = range(
    5)
OPTION_0, OPTION_1, OPTION_2, OPTION_3, VIEW_REMINDERS, VIEW_REMINDER, EDIT_SETTINGS, BACK = range(
    8)

# Global Keyboards and Markups
remind_setting_keyboard = [
    [
        InlineKeyboardButton(
            "Enable for days with tasks", callback_data=str(OPTION_1) + '#' + str(1)),
    ],
    [
        InlineKeyboardButton(
            "Disable completely", callback_data=str(OPTION_1) + '#' + str(0))]
]

remind_setting_markup = InlineKeyboardMarkup(
    remind_setting_keyboard)


timezone_setting_keyboard = [
    ["Singapore"],
    ["-7", "-8", "-9"],
    ["+7", "+9", "+10"]
]
timezone_setting_markup = ReplyKeyboardMarkup(
    timezone_setting_keyboard)

wake_setting_keyboard = [
    [
        InlineKeyboardButton(
            "5am", callback_data=str(OPTION_3) + '#' + str(5)),
        InlineKeyboardButton(
            "6am", callback_data=str(OPTION_3) + '#' + str(6)),
    ],
    [
        InlineKeyboardButton(
            "7am", callback_data=str(OPTION_3) + '#' + str(7)),
        InlineKeyboardButton(
            "8am", callback_data=str(OPTION_3) + '#' + str(8)),
    ],
    [
        InlineKeyboardButton(
            "9am", callback_data=str(OPTION_3) + '#' + str(9)),
        InlineKeyboardButton(
            "10am", callback_data=str(OPTION_3) + '#' + str(10)),
    ]
]

wake_setting_markup = InlineKeyboardMarkup(
    wake_setting_keyboard)

invalid_deadline_keyboard = [
    [
        InlineKeyboardButton(
            "Okay, fine :(", callback_data=str(BACK)),
    ]
]

invalid_deadline_markup = InlineKeyboardMarkup(invalid_deadline_keyboard)

scheduler_client = boto3.client('scheduler')


def put_event(time, detail):
    response = scheduler_client.create_schedule(
        Description='AnelaBot remind once scheduler',
        FlexibleTimeWindow={
            'Mode': 'OFF'
        },
        GroupName='AnelaBotSchedulegroup',
        Name='Scheduled' + detail['reminder_id'] + detail['token'],
        ScheduleExpression='at(' + time.strftime('%Y-%m-%dT%H:%M:%S)'),
        ScheduleExpressionTimezone='UTC',
        State='ENABLED',
        Target={
            'Arn': os.environ.get('AnelaBotHandlerARN'),
            # 'EventBridgeParameters': {
            #     'DetailType': 'Custom AnelaBot detail',
            #     'Source': 'anelabot.lambda.main',
            # },
            'Input': json.dumps(detail),
            'RetryPolicy': {
                'MaximumEventAgeInSeconds': 60,
                'MaximumRetryAttempts': 3
            },
            'RoleArn': os.environ.get('AnelaBotSchedulerARN'),
        }
    )
    return response


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user_name = update.message.from_user.first_name
    user_id = update.message.chat_id

    user = UserObject.get_user(user_id)

    if user:
        await update.message.reply_text("Welcome back {username}!".format(username=user_name))
    else:
        user = UserObject(user_id=user_id)

        if not user.save():
            await update.message.reply_text(text="Sorry, an unexpected error occured. Please contact admin")
            return ConversationHandler.END

        start_message = await update.message.reply_text("Welcome to AnelaBot!!\n\n<b>Purpose:</b>\n - I am a reminder bot that allows you to create reminders through natural language processing (NLP).\n - If there are reminders set for a day, I will send a message to remind you on the morning of the day itself.\n - I ignore all messages not intended to be a reminder.\n - I intend to be a upgrade to the practice of 'Chat with myself' i.e. sending messages to yourself for future reference. You can sent messages to me, which I will ignore unless the syntax of a reminder is detected.\n\n<b>How to use:</b>\n - In /settings, you can set your timezone and preferred 'wake up time', the time when daily updates will be sent.\n - In /view_reminders, you can view all your reminders (sorted by deadline), and edit them.\n - You can create reminders by typing one, following the reminder syntax. E.g. try this: start studying today 3pm \n - You can send text for future references like links, strings etc., which I will ignore.\n\n<b>Reminder syntax:</b>\n - Bring keycard today/tomorrow/tmr/next day/following day\n - Develop code this wed/on wednesday\n - Play frisbee next/following sunday\n - Scholarship interview on 27 feb 2022\n - Christmas party on 25 dec(ember)\n\n<b>Privacy:</b> I only save information from messages deemed as reminders, to remind you.\n\n<b>p.s.:</b> This deployment is hosted with free-tier AWS services which may take ~3s between cold starts as well as delays up to 1min in reminders.", parse_mode=constants.ParseMode.HTML)
        await context.bot.pin_chat_message(chat_id=user_id, message_id=start_message.message_id)
    return USER_ROUTE


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.delete_message()
    return USER_ROUTE


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    user_id = update.effective_chat.id
    user = UserObject.get_user(user_id)
    query = update.callback_query

    settings_keyboard = [
        [
            InlineKeyboardButton("Timezone ({}.00 GMT)".format(user.timezone_offset), callback_data=str(
                OPTION_2)),
            InlineKeyboardButton(
                "Wake up time ({}am)".format(user.wake_time + user.timezone_offset), callback_data=str(OPTION_3))
        ],
        [
            InlineKeyboardButton(
                "Daily reminders ({})".format(user.remind_setting_str()), callback_data=str(OPTION_1)),
            InlineKeyboardButton(
                "Back", callback_data=str(BACK))
        ],
    ]

    settings_markup = InlineKeyboardMarkup(settings_keyboard)
    if query:
        await query.edit_message_text("What settings do you want to change?\n\n1. Timezone. Determines when you receive your updates.\n2. Wake up time. Determines when in the morning you receive your daily updates.\n3. Enable/disable reminders. Choose to enable or disable everyday reminders, if there are tasks scheduled.", reply_markup=settings_markup)
    else:
        await context.bot.sendMessage(user_id, "What settings do you want to change?\n\n1. Timezone. Determines when you receive your updates.\n2. Wake up time. Determines when you receive your daily updates.\n3. Reminding pattern. Determines on what days you will receive daily updates of the day's tasks, if there are tasks scheduled,.", reply_markup=settings_markup)

    return SETTINGS_ROUTE


async def choose_remind_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    query = update.callback_query

    await query.edit_message_text("Choose on what days would I remind you of your tasks of the day. Note that I'll only send you daily updates if there are tasks scheduled.", reply_markup=remind_setting_markup)

    return SETTINGS_ROUTE


async def edit_remind_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    user_id = update.effective_chat.id
    user = UserObject.get_user(user_id)

    query = update.callback_query
    user.remind_setting = int(query.data[2:])
    user.save()

    return await settings_menu(update, context)


async def choose_timezone_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    query = update.callback_query
    await query.delete_message()
    await context.bot.send_message(update.effective_chat.id, "Are you from Singapore? Else, find your timezone offset from UTC and input it here (e.g. -8 for California).", reply_markup=timezone_setting_markup)
    return TYPE_SETTINGS_ROUTE


async def edit_timezone_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    text = update.message.text
    if text == "Singapore":
        offset = 8
    else:
        try:
            offset = int(text)
            if offset > 14 or offset < -12:
                raise ValueError
        except ValueError:
            offset = None
    if offset:
        user_id = update.effective_chat.id
        user = UserObject.get_user(user_id)
        user.timezone_offset = offset
        user.save()
        await context.bot.send_message(chat_id=user_id, text="You have selected {}.00 UTC as your timezone!".format(offset), reply_markup=ReplyKeyboardRemove())
        return await settings_menu(update, context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm sorry, you have given an invalid timezone. Please try again.")
        return TYPE_SETTINGS_ROUTE


async def choose_wake_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    query = update.callback_query

    await query.edit_message_text("Choose when I will send you your daily updates.", reply_markup=wake_setting_markup)

    return SETTINGS_ROUTE


async def edit_wake_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creates ReplyKeyboard for userType, redirect ROUTES"""
    query = update.callback_query
    user_id = update.effective_chat.id
    wake_time = int(query.data[2:])

    user = UserObject.get_user(user_id)
    user.wake_time = wake_time - user.timezone_offset
    user.save()

    return await settings_menu(update, context)


async def view_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Redirect REMINDER_ROUTE"""
    user_id = update.effective_chat.id
    keyboard = list()

    query = update.callback_query
    user_data = context.user_data
    page_data = user_data.get('page_data')

    if query:
        try:
            page_number = int(query.data[2:])
        except ValueError:
            page_number = 0
    else:
        await update.message.delete()
        page_number = 0

    if page_number:
        exclusive_start_key = page_data[page_number]
    else:
        exclusive_start_key = None

    data = ReminderObject.reminders_by_page(user_id, exclusive_start_key)
    last_evaluated_key = data['last_evaluated_key']

    for i in data['reminders']:
        keyboard.append([InlineKeyboardButton(
            i.text_limited(), callback_data=str(VIEW_REMINDER) + '#' + str(i.id))])

    if page_number == 0:
        if last_evaluated_key:
            page_data = {1: last_evaluated_key}
            keyboard.append([
                InlineKeyboardButton(
                    "Next page", callback_data=str(VIEW_REMINDERS) + '#' + str(page_number + 1)),
                InlineKeyboardButton(
                    "Return", callback_data=str(BACK))])
        else:
            keyboard.append([InlineKeyboardButton(
                "Return", callback_data=str(BACK))])
    else:
        bottom_keyboard = list()
        bottom_keyboard.append(InlineKeyboardButton(
            "<<<", callback_data=str(VIEW_REMINDERS) + '#' + str(page_number - 1)))
        bottom_keyboard.append(InlineKeyboardButton(
            "Return", callback_data=str(BACK)))
        if last_evaluated_key:
            page_data[page_number + 1] = last_evaluated_key
            bottom_keyboard.append(InlineKeyboardButton(
                ">>>", callback_data=str(VIEW_REMINDERS) + '#' + str(page_number + 1)))
        keyboard.append(bottom_keyboard)

    context.user_data.update({'page_data': page_data})

    reply_markup = InlineKeyboardMarkup(keyboard)

    if data['reminders']:
        if query:
            await query.edit_message_text(text="Here are your reminders! Edit them here!", reply_markup=reply_markup)
        else:
            await context.bot.sendMessage(chat_id=user_id, text="Here are your reminders! Edit them here!", reply_markup=reply_markup)
    else:
        if query:
            await query.edit_message_text(text="You have no reminders right now. Feel free return and add one now!", reply_markup=reply_markup)
        else:
            await context.bot.sendMessage(chat_id=user_id, text="You have no reminders right now. Feel free return and add one now!", reply_markup=reply_markup)
    return REMINDER_ROUTE


async def view_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    reminder_id = query.data[2:]

    reminder = ReminderObject.get_reminder(reminder_id)

    if query.message:
        keyboard = [
            [InlineKeyboardButton(
                "Edit parameters", callback_data=str(OPTION_1) + '#' + str(reminder.id))],
            [
                InlineKeyboardButton(
                    "Delete", callback_data=str(OPTION_0) + '#' + str(reminder.id)),
                InlineKeyboardButton(
                    "Done", callback_data=str(VIEW_REMINDERS))
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="This is your reminder:\n\n{}\nDeadline: {}\nTime by: {}".format(reminder.text, reminder.deadline_str(), reminder.time_by), reply_markup=reply_markup
                                      )
    else:
        keyboard = [
            [InlineKeyboardButton(
                "Edit parameters", callback_data=str(OPTION_1) + '#' + str(reminder.id))],
            [
                InlineKeyboardButton(
                    "Delete", callback_data=str(OPTION_0) + '#' + str(reminder.id)),
                InlineKeyboardButton(
                    "Done", callback_data=str(BACK))
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Based on the date and/or time captured, I have created a reminder:\n\n{}\nDeadline: {}\nTime by: {}\n\n Do you want to change any of these fields?".format(reminder.text, reminder.deadline_str(), reminder.time_by), reply_markup=reply_markup
                                       )
    return REMINDER_ROUTE


async def edit_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    reminder_id = query.data[2:]
    payload = {
        "reminder_id": reminder_id
    }
    context.user_data.update(payload)

    await query.edit_message_text(text="Please specify your reminder again using the syntax! Or /back to cancel edit action.")

    return EDIT_REMINDER_ROUTE


async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    reminder_id = query.data[2:]

    reminder = ReminderObject.get_reminder(reminder_id)
    reminder.delete()

    update.callback_query.data = str(VIEW_REMINDER)

    return await view_reminders(update, context)


async def edit_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_chat.id
    user = UserObject.get_user(user_id)
    reminder_id = context.user_data['reminder_id']
    context.user_data.clear()
    text = update.message.text

    data = match_date(text)

    if data:
        time_by = data['time_by']
        deadline = data['deadline']

        now = datetime.datetime.utcnow()
        local_now = now + datetime.timedelta(hours=user.timezone_offset)
        if local_now.date() > now.date():
            new_date = deadline + datetime.timedelta(days=1)
            if new_date <= local_now.date() + datetime.timedelta(days=1):
                deadline = new_date
        elif local_now.date() < now.date():
            new_date = deadline - datetime.timedelta(days=1)
            if new_date <= local_now.date() + datetime.timedelta(days=1):
                deadline = new_date

        if time_by:
            time = datetime.datetime.combine(
                deadline, time_by) - datetime.timedelta(hours=user.timezone_offset)
            if time < now:
                await context.bot.send_message(chat_id=user_id, text="Sorry, your deadline is in the past! I'm not a time machine...", reply_markup=invalid_deadline_markup)
                return REMINDER_ROUTE
            detail = {"action": "remind_once",
                      "reminder_id": reminder_id,
                      "text": data['text'],
                      "chat_id": user_id,
                      "time_by": time_by.strftime("%H%M"),
                      "token": str(uuid.uuid4())[:8]
                      }
            put_event(time=time, detail=detail)
        else:
            if deadline <= local_now.date():
                await context.bot.send_message(chat_id=user_id, text="Sorry, for reminders without time specified, do set them from tomorrow onwards! If you wanna set a reminder for today, please specify a time for me to remind you on!!", reply_markup=invalid_deadline_markup)
                return REMINDER_ROUTE

        ReminderObject(id=reminder_id, user_id=user_id,
                       text=data['text'], deadline=deadline, time_by=time_by).save()

        update.callback_query = CallbackQuery(
            id=None, from_user=None, chat_instance=None, data=str(VIEW_REMINDER) + '#' + str(reminder_id))
        return await view_reminder(update, context)


async def create_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_chat.id
    user = UserObject.get_user(user_id)
    text = update.message.text
    data = match_date(text)

    if data:
        time_by = data['time_by']
        deadline = data['deadline']

        now = datetime.datetime.utcnow()
        local_now = now + datetime.timedelta(hours=user.timezone_offset)
        if local_now.date() > now.date():
            new_date = deadline + datetime.timedelta(days=1)
            if new_date <= local_now.date() + datetime.timedelta(days=1):
                deadline = new_date
        elif local_now.date() < now.date():
            new_date = deadline - datetime.timedelta(days=1)
            if new_date <= local_now.date() + datetime.timedelta(days=1):
                deadline = new_date

        if time_by:
            time = datetime.datetime.combine(
                deadline, time_by) - datetime.timedelta(hours=user.timezone_offset)
            if time < now:
                await context.bot.send_message(chat_id=user_id, text="Sorry, your deadline is in the past! I'm not a time machine...", reply_markup=invalid_deadline_markup)
                return REMINDER_ROUTE

            reminder = ReminderObject(
                user_id=user_id, text=data['text'], deadline=deadline, time_by=time_by).save()

            detail = {"action": "remind_once",
                      "reminder_id": reminder.id,
                      "text": data['text'],
                      "chat_id": user_id,
                      "time_by": time_by.strftime("%H%M"),
                      "token": str(uuid.uuid4())[:8]
                      }
            put_event(time=time, detail=detail)
        else:
            if deadline <= local_now.date():
                await context.bot.send_message(chat_id=user_id, text="Sorry, for reminders without time specified, do set them from tomorrow onwards! If you wanna set a reminder for today, please specify a time for me to remind you on!!", reply_markup=invalid_deadline_markup)
                return REMINDER_ROUTE
            reminder = ReminderObject(
                user_id=user_id, text=data['text'], deadline=deadline, time_by=time_by).save()

        update.callback_query = CallbackQuery(
            id=None, from_user=None, chat_instance=None, data=str(VIEW_REMINDER) + '#' + str(reminder.id))
        return await view_reminder(update, context)

# contact, get_feedback, unknown and exit actions


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unknown handler"""
    await update.message.reply_text("Sorry, I do not understand this command.\n\n Available commands:\n/view_reminders: View all reminders you have.\n/settings: Edit user settings, like timezone, wake time, enable/disable daily updates.")


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unknown handler"""
    await update.message.reply_text("Sorry, you can't add reminders or pass commands while handling another action.")


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the conversation."""

    await update.message.reply_text("Exiting. Until next time!",
                                    reply_markup=ReplyKeyboardRemove(),
                                    )
    return ConversationHandler.END
