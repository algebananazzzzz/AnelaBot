# AnelaBot
## Writeup:
AnelaBot(telegram) is a telegram bot application that allows you to create reminders through natural language processing (NLP).

# Features:
- If there are reminders set for a day, I will send a message to remind you on the morning of the day itself.
- Ignores all messages not intended to be a reminder.
- Intended to be a upgrade to the practice of 'Chat with myself' i.e. sending messages to yourself for future reference. Sent messages are ignored unless the syntax of a reminder is detected.

# How to use:
- In /settings, you can set your timezone and preferred 'wake up time', the time when daily updates will be sent.
- In /view_reminders, you can view all your reminders (sorted by deadline), and edit them.
- Create reminders by typing one, following the reminder syntax. E.g. start studying today 3pm, which the bot will send a reminder message to "start studying" on 3pm today
- You can send text for future references like links, strings etc., which I will ignore
## Reminder syntax:
- Bring keycard today/tomorrow/tmr/next day/following day
- Develop code this wed/on wednesday
- Play frisbee next/following sunday
- Scholarship interview on 27 feb 2022
- Christmas party on 25 dec(ember)

# Deployment
AnelaBot is currently [deployed on telegram](https://t.me/AnelaBot) with free-tier AWS services (Lambda, Elasticache, Dynamodb and EventBridge)
It may take ~3s between cold starts as well as delays up to 1min in reminders.
