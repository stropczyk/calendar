from datetime import datetime, date

from .db_service import db
from .email_sender import send_reminder


def reminder():
    today = str(date.today())

    today_events = db.cx.calendar.events.find({'event_date': today, 'reminded': False})

    now = datetime.now()

    for event in today_events:
        event_dt = datetime.strptime(event['event_datetime'], '%Y-%m-%d %H:%M')
        delta = event_dt - now
        delta_min = delta.seconds / 60
        if 34 >= delta_min > 25:
            send_reminder(event['recipient_mail'], event['title'], event['event_date'], event['event_time'])
            db.cx.calendar.events.update_one(
                {'_id': event['_id']},
                {"$set": {'reminded': True}})
