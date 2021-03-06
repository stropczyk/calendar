from flask import Flask
from flask_apscheduler import APScheduler

from main.action_handler import reminder

app = Flask(__name__)
scheduler = APScheduler()


def job():
    reminder()


if __name__ == '__main__':
    scheduler.add_job(id='job', func=job, trigger='interval', minutes=5)
    scheduler.start()

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
