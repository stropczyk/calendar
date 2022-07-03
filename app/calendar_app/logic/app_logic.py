import datetime
import pytz
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from uuid import uuid4
from flask import session


CALENDAR_ID = os.getenv('CALENDAR_ID')

SCOPES = 'https://www.googleapis.com/auth/calendar'

credentials = None

if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        credentials = pickle.load(token)

if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes=SCOPES)
        credentials = flow.run_local_server(port=0)

    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)

g_service = build('calendar', 'v3', credentials=credentials)


def generate_timeMin_timeMax(date):
    warsaw = pytz.timezone('Europe/Warsaw')
    if date == 'today':
        dateMin = datetime.date.today()
        dateMax = datetime.date.today() + datetime.timedelta(days=1)
    elif date == 'tomorrow':
        dateMin = datetime.date.today() + datetime.timedelta(days=1)
        dateMax = datetime.date.today() + datetime.timedelta(days=2)

    time = datetime.time()
    timeMin = datetime.datetime.combine(dateMin, time, tzinfo=warsaw).isoformat()
    timeMax = datetime.datetime.combine(dateMax, time, tzinfo=warsaw).isoformat()

    return timeMin, timeMax


def get_events_from_calendar(service, calendar, timeMin, timeMax):
    events_result = service.events().list(calendarId=calendar, timeMin=timeMin, timeMax=timeMax).execute()
    events = events_result.get('items', [])
    for event in events:
        date_time = event['start']['dateTime']
        tz = event['start']['timeZone']
        dt = datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S%z")
        now_in_warsaw = dt.astimezone(pytz.timezone(tz))
        event['start']['local'] = str(now_in_warsaw)
    return events


def generate_today_available_hours(events):
    hours = [*range(8, 22, 1)]
    minutes = ['00', '30']

    all_hours = [{"text": f'0{x}:{y}', "value": f'0{x}:{y}'} if x < 10
                 else {"text": f'{x}:{y}', "value": f'{x}:{y}'}
                 for x in hours for y in minutes]

    next_meeting = datetime.datetime.now() + datetime.timedelta(hours=1)
    hour = next_meeting.hour
    minute = next_meeting.minute
    next_meeting_time = f'{hour}:{minute}'

    available_hours = [i for i in all_hours if i['value'] >= next_meeting_time]

    for i in all_hours:
        for event in events:
            if i['value'] == event['start']['local'][11:16]:
                try:
                    available_hours.remove(i)
                except ValueError:
                    pass

    action_id = 1

    for i in available_hours:
        i['action_id'] = f'{action_id}'
        action_id += 1

    return available_hours


def generate_tomorrow_available_hours(events):
    hours = [*range(8, 22, 1)]
    minutes = ['00', '30']

    all_hours = [{"text": f'0{x}:{y}', "value": f'0{x}:{y}'} if x < 10
                 else {"text": f'{x}:{y}', "value": f'{x}:{y}'}
                 for x in hours for y in minutes]

    available_hours = all_hours.copy()

    for i in all_hours:
        for event in events:
            if i['value'] == event['start']['local'][11:16]:
                available_hours.remove(i)

    action_id = 1

    for i in available_hours:
        i['action_id'] = f'{action_id}'
        action_id += 1

    return available_hours


def build_event(who, mail, title, m_time, date):

    if 'today' in date:
        meeting_date = str(datetime.date.today())
    elif 'tomorrow' in date:
        meeting_date = str(datetime.date.today() + datetime.timedelta(days=1))
    else:
        meeting_date = date

    start_time_object = datetime.datetime.strptime(m_time, '%H:%M')
    start_hour = start_time_object.hour
    start_minute = start_time_object.minute

    end_time_object = datetime.datetime.strptime(m_time, '%H:%M') + datetime.timedelta(minutes=30)
    end_hour = end_time_object.hour
    end_minute = end_time_object.minute

    start_datetime = f'{meeting_date}T{start_hour}:{start_minute}:00'
    end_datetime = f'{meeting_date}T{end_hour}:{end_minute}:00'
    event = {
        'summary': title,
        'attendees': [
            {'displayName': who,
             'email': mail}
        ],
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Europe/Warsaw'
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Europe/Warsaw'
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"{uuid4().hex}",
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                }
            }
        }
    }

    return event


def get_access_token(string):
    str_divided = string.split('&')
    access_token = str_divided[0]
    at_divided = access_token.split('=')
    at_value = at_divided[1]
    return at_value


def get_user_info(creds):
    user_info_service = build(
        serviceName='oauth2', version='v2',
        credentials=creds)

    user_info = user_info_service.userinfo().get().execute()

    return user_info


def clear_session():
    session.pop('event_date', None)
    session.pop('event_time', None)
    session.pop('login', None)
    session.pop('email', None)
    session.pop('code', None)
