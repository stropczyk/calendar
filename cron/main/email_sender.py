import smtplib
import os

from email.message import EmailMessage

MAIL_ADDRESS = os.getenv('MAIL_ADDRESS')
MAIL_PASSWORD = os.getenv('MAIL_PWD')

smtp = smtplib.SMTP_SSL('mail40.mydevil.net', 465)

smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)


def send_reminder(recipient, title, event_date, event_time):
    msg = EmailMessage()
    msg['Subject'] = title
    msg['From'] = MAIL_ADDRESS
    msg['To'] = recipient
    msg.set_content(f"Hello!\n"
                    f"Your's meeting is going to start in next 30 minutes.\n"
                    f"Meeting starts on {event_date} at {event_time}.")

    smtp.send_message(msg)
