import os
import json
import handlers
import asyncio
from mypersistence import MyPersistence
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    PersistenceInput,
)

# Stages + Callback data
USER_ROUTE, REMINDER_ROUTE, EDIT_REMINDER_ROUTE, SETTINGS_ROUTE, TYPE_SETTINGS_ROUTE = range(
    5)
OPTION_0, OPTION_1, OPTION_2, OPTION_3, VIEW_REMINDERS, VIEW_REMINDER, EDIT_SETTINGS, BACK = range(
    8)


persistence = MyPersistence(function_name=os.environ.get("REDIS_LAMBDA_FUNCTION"), redis_key=os.environ.get("REDIS_KEY"),
                            store_data=PersistenceInput(chat_data=False, bot_data=False), update_interval=60)
application = Application.builder().token(
    os.environ.get('TOKEN')).persistence(persistence).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", handlers.start)],
    states={
        USER_ROUTE: [
            CommandHandler('settings', handlers.settings_menu),
            CommandHandler('view_reminders', handlers.view_reminders),
            CommandHandler('exit', handlers.exit),
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           handlers.create_reminder_text),
            MessageHandler(filters.COMMAND,
                           handlers.unknown)
        ],

        REMINDER_ROUTE: [
            # Delete message displaying all remidners
            CallbackQueryHandler(
                handlers.back, pattern="^" + str(BACK) + "$"),
            CallbackQueryHandler(
                handlers.view_reminders, pattern="^" + str(VIEW_REMINDERS)),
            CallbackQueryHandler(
                handlers.view_reminders, pattern="^" + str(VIEW_REMINDERS) + "#\d+$"),
            CallbackQueryHandler(
                handlers.view_reminder, pattern="^" + str(VIEW_REMINDER) + "#[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
            CallbackQueryHandler(
                handlers.edit_reminder, pattern="^" + str(OPTION_1) + "#[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
            CallbackQueryHandler(
                handlers.delete_reminder, pattern="^" + str(OPTION_0) + "#[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
            MessageHandler(filters.TEXT, handlers.unknown_text)

        ],
        EDIT_REMINDER_ROUTE: [
            CallbackQueryHandler(
                handlers.back, pattern="^" + str(BACK) + "$"),
            CommandHandler('back', handlers.view_reminder),
            MessageHandler(filters.TEXT, handlers.edit_reminder_text)
        ],
        SETTINGS_ROUTE: [
            CallbackQueryHandler(
                handlers.back, pattern="^" + str(BACK) + "$"),
            CallbackQueryHandler(
                handlers.choose_timezone_setting, pattern="^" + str(OPTION_2) + "$"),
            CallbackQueryHandler(
                handlers.choose_remind_setting, pattern="^" + str(OPTION_1) + "$"),
            CallbackQueryHandler(
                handlers.edit_remind_setting, pattern="^" + str(OPTION_1) + "#\d+$"),
            CallbackQueryHandler(
                handlers.choose_wake_setting, pattern="^" + str(OPTION_3) + "$"),
            CallbackQueryHandler(
                handlers.edit_wake_setting, pattern="^" + str(OPTION_3) + "#\d+$"),
            MessageHandler(filters.TEXT, handlers.unknown_text)
        ],
        TYPE_SETTINGS_ROUTE: [
            MessageHandler(
                filters.Regex("^Back$"), handlers.settings_menu
            ),
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           handlers.edit_timezone_setting)
        ],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^Exit$"), exit)
    ],
    name="anela_conversation",
    persistent=True,
)
application.add_handler(conv_handler)


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))


async def main(event, context):
    try:
        if "keep_warm" in event:
            return {
                'statusCode': 200,
                'body': 'Warmed'
            }
        await application.initialize()
        await application.process_update(Update.de_json(json.loads(event["body"]), application.bot))
        await application.update_persistence()
        await persistence.flush()
        return {
            'statusCode': 200,
            'body': 'Success'
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 'Failure'
        }
