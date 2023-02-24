import uuid
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

resource = boto3.resource('dynamodb')
user_table = resource.Table('users')
reminder_table = resource.Table('reminders')


def create_tables():
    try:
        resource.create_table(
            TableName='users',
            KeySchema=[
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                }

            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'wakeTime',
                    'AttributeType': 'N'
                },
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'userIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'wakeTime',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'userId',
                            'KeyType': 'RANGE'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 2,
                'WriteCapacityUnits': 2
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pass
        else:
            raise ClientError(e.response)
    try:
        resource.create_table(
            TableName='reminders',
            KeySchema=[
                {
                    'AttributeName': 'Id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'Id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'uniqueDeadline',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'remindIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'userId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'uniqueDeadline',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 2,
                        'WriteCapacityUnits': 2
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pass
        else:
            raise ClientError(e.response)


def add_user(user_id):
    data = user_table.put_item(
        Item={
            'userId': user_id,
            'remindSetting': 1,
            'timezoneOffset': 8,
            'wakeTime': 0
        }
    )
    return data


def update_user(user_id, remind_setting, timezone_offset, wake_time):
    user_table.update_item(
        AttributeUpdates={
            'remindSetting': {
                'Value': remind_setting,
                'Action': 'PUT'
            },
            'timezoneOffset': {
                'Value': timezone_offset,
                'Action': 'PUT'
            },
            'wakeTime': {
                'Value': wake_time,
                'Action': 'PUT'
            }
        },
        Key={
            'userId': user_id
        },
        ReturnValues='ALL_NEW',
    )

    return True


def query_user(user_id):
    data = user_table.get_item(
        Key={
            'userId': user_id
        }
    )
    try:
        return data['Item']
    except KeyError:
        return None


def query_users(wake_time=None):
    """ query user tuple based on the user id """
    if wake_time is not None:
        data = user_table.query(
            IndexName='userIndex', KeyConditionExpression=Key('wakeTime').eq(wake_time))
    else:
        data = user_table.scan()

    return data['Items']


def add_reminder(user_id, text, deadline, time_by):
    id = str(uuid.uuid1())
    item_dict = {
        'Id': id,
        'userId': user_id,
        'text': text,
        'uniqueDeadline': deadline + '&' + id,
        'timeBy': time_by
    }
    # if time_by:
    #     item_dict['timeBy'] = time_by
    reminder_table.put_item(
        Item=item_dict
    )
    return id


def update_reminder(id, text, deadline, time_by):
    reminder_table.update_item(
        AttributeUpdates={
            'text': {
                'Value': text,
                'Action': 'PUT'
            },
            'uniqueDeadline': {
                'Value': deadline + '&' + id,
                'Action': 'PUT'
            },
            'timeBy': {
                'Value': time_by,
                'Action': 'PUT'
            }
        },
        Key={
            'Id': id
        },
        ReturnValues='ALL_NEW',
    )


def query_reminder(id):
    data = reminder_table.get_item(
        Key={
            'Id': id
        }
    )
    try:
        return data['Item']
    except KeyError:
        return None


def query_reminders(user_id, deadline=None):
    if deadline:
        data = reminder_table.query(
            IndexName='remindIndex',
            KeyConditionExpression=Key('userId').eq(
                user_id) & Key('uniqueDeadline').begins_with(deadline)
        )
    else:
        data = reminder_table.query(
            IndexName='remindIndex',
            KeyConditionExpression=Key('userId').eq(user_id)
        )

    return data['Items']


def query_reminders_page(user_id, last_evaluated_key=None):
    """ query user tuple based on the user id """
    if last_evaluated_key:
        last_evaluated_key = {'uniqueDeadline': last_evaluated_key,
                              'userId': user_id, 'Id': last_evaluated_key.split('&')[1]}
        data = reminder_table.query(
            IndexName='remindIndex',
            Limit=11,
            ExclusiveStartKey=last_evaluated_key,
            KeyConditionExpression=Key('userId').eq(user_id)
        )
    else:
        data = reminder_table.query(
            IndexName='remindIndex',
            Limit=11,
            KeyConditionExpression=Key('userId').eq(user_id)
        )
    reminders = data['Items']
    if len(reminders) == 11:
        last_evaluated_key = reminders[9]['uniqueDeadline']
        reminders.pop()
    else:
        last_evaluated_key = None

    return {'reminders': reminders, 'LastEvaluatedKey': last_evaluated_key}


def delete_reminder(id):
    reminder_table.delete_item(
        Key={
            'Id': id
        }
    )
    return True


def delete_reminders(user_id, deadline):
    data = reminder_table.query(IndexName='remindIndex', KeyConditionExpression=Key(
        'userId').eq(user_id) & Key('uniqueDeadline').begins_with(deadline))['Items']
    with reminder_table.batch_writer() as batch:
        for item in data:
            batch.delete_item(Key={
                'Id': item['Id']
            })
    return True
