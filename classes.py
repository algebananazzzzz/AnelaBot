import dynamodb
import datetime


class UserObject(object):
    """docstring for UserObject."""
    ADMIN, USER, STRANGER = range(3)

    def __init__(self, user_id, remind_setting=1, timezone_offset=None, wake_time=None):
        super(UserObject, self).__init__()
        self.user_id = user_id
        self.remind_setting = remind_setting
        self.timezone_offset = timezone_offset
        self.wake_time = wake_time

    def get_user(user_id):
        user = dynamodb.query_user(user_id)

        if user:
            return UserObject(user_id=user_id, remind_setting=int(user['remindSetting']), timezone_offset=int(user['timezoneOffset']), wake_time=int(user['wakeTime']))
        else:
            return None

    def users(wake_time=None):
        if wake_time:
            users = dynamodb.query_users(wake_time)
        else:
            users = dynamodb.query_users()
        data = list()
        for user in users:
            data.append(UserObject(user_id=user['userId'], remind_setting=int(
                user['remindSetting']), timezone_offset=int(user['timezoneOffset']), wake_time=int(user['wakeTime'])))
        return data

    # def tupled(self):
    #     return tuple(self.__dict__.values())

    def remind_setting_str(self):
        return ['Disabled', 'Enabled'][int(self.remind_setting)]

    def reminders(self, deadline=None):
        if deadline:
            deadline = deadline.strftime('%d#%m#%Y')
        reminders = dynamodb.query_reminders(self.user_id, deadline)

        data = list()
        for i in reminders:
            unique_deadline = i['uniqueDeadline'].split('&')
            reminder = ReminderObject(user_id=i['userId'], text=i['text'], deadline=datetime.datetime.strptime(
                unique_deadline[0], '%d#%m#%Y').date(), id=unique_deadline[1])
            if i['timeBy']:
                reminder.time_by = datetime.datetime.strptime(
                    i['timeBy'], '%H#%M').time()
            data.append(reminder)

        return data

    def save(self):
        user = dynamodb.query_user(self.user_id)
        if user:
            dynamodb.update_user(user_id=self.user_id, remind_setting=self.remind_setting,
                                 timezone_offset=self.timezone_offset, wake_time=self.wake_time)
        else:
            dynamodb.add_user(user_id=self.user_id)
        return True


class ReminderObject(object):
    """docstring for ReminderObject."""
    ACADEMICS, CCA, WORK, FAMILY, SCHEDULES, TODO, FUN_STUFF, OTHERS = range(8)

    def __init__(self, user_id, text, deadline=datetime.date.today(), time_by=None, id=None):
        super(ReminderObject, self).__init__()
        self.user_id = user_id
        self.text = text
        self.deadline = deadline
        self.time_by = time_by
        self.id = id

    # def tupled(self):
    #     return tuple(self.__dict__.values())

    def text_limited(self):
        text = self.text
        if len(text) > 30:
            return text[:30] + '...'
        else:
            return text

    def deadline_str(self):
        return self.deadline.strftime('%d %b %y')

    def get_reminder(id):
        i = dynamodb.query_reminder(id)

        if i:
            unique_deadline = i['uniqueDeadline'].split('&')
            reminder = ReminderObject(user_id=i['userId'], text=i['text'], deadline=datetime.datetime.strptime(
                unique_deadline[0], '%d#%m#%Y').date(), id=unique_deadline[1])
            if i['timeBy']:
                reminder.time_by = datetime.datetime.strptime(
                    i['timeBy'], '%H#%M').time()
            return reminder
        else:
            raise Exception("No reminder object associated")

    def reminders_by_page(user_id, last_evaluated_key=None):
        query = dynamodb.query_reminders_page(user_id, last_evaluated_key)

        data = list()
        for i in query['reminders']:
            unique_deadline = i['uniqueDeadline'].split('&')
            reminder = ReminderObject(user_id=i['userId'], text=i['text'], deadline=datetime.datetime.strptime(
                unique_deadline[0], '%d#%m#%Y').date(), id=unique_deadline[1])
            if i['timeBy']:
                reminder.time_by = datetime.datetime.strptime(
                    i['timeBy'], '%H#%M').time()
            data.append(reminder)
        return {'reminders': data, 'last_evaluated_key': query['LastEvaluatedKey']}

    def save(self):
        if self.time_by:
            time_by = self.time_by.strftime('%H#%M')
        else:
            time_by = None
        if self.id:
            dynamodb.update_reminder(id=self.id, text=self.text, deadline=self.deadline.strftime(
                '%d#%m#%Y'), time_by=time_by)
        else:
            self.id = dynamodb.add_reminder(
                user_id=self.user_id, text=self.text, deadline=self.deadline.strftime('%d#%m#%Y'), time_by=time_by)
        return self

    def delete_by_params(user_id, deadline):
        if not isinstance(deadline, datetime.date):
            raise TypeError(
                "Expected deadline of type datetime.date, got some other type instead.")
        dynamodb.delete_reminders(user_id=user_id, deadline=deadline)
        return True

    def delete(self):
        dynamodb.delete_reminder(self.id)
        return True
