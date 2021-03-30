import smtplib
import os

from email.message import EmailMessage

MAIL_ADDRESS = os.getenv('MAIL_ADDRESS')
MAIL_PASSWORD = os.getenv('MAIL_PWD')


def send_confirmation(recipient, title, event_date, event_time):
    msg = EmailMessage()
    msg['Subject'] = title
    msg['From'] = MAIL_ADDRESS
    msg['To'] = recipient
    msg.set_content(f'This is confirmation of your meeting.\n'
                    f'Meeting starts on {event_date} at {event_time}.')

    smtp = smtplib.SMTP_SSL('mail40.mydevil.net', 465)
    smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
    smtp.send_message(msg)
