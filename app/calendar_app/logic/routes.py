import requests

from datetime import (
    date,
    timedelta,
)
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from github import Github
from google_auth_oauthlib.flow import (
    Flow,
    InstalledAppFlow,
)

from .app_logic import (
    CALENDAR_ID,
    build_event,
    clear_session,
    generate_timeMin_timeMax,
    generate_today_available_hours,
    generate_tomorrow_available_hours,
    get_access_token,
    get_events_from_calendar,
    get_user_info,
)
from .app_logic import g_service as srv
from .email_sender import send_confirmation
from calendar_app.db.utils import db
from calendar_app.github_bot.routes import (
    gh_client_id,
    gh_client_secret,
)


main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home", methods=['GET'])
def home():
    clear_session()
    return render_template('home.html', title='Home')


@main.route("/calendar", methods=['GET', 'POST'])
def calendar():
    clear_session()
    service = srv

    today = 'today'
    time_min, time_max = generate_timeMin_timeMax(today)
    events_today = get_events_from_calendar(service, CALENDAR_ID, time_min, time_max)
    available_hours = generate_today_available_hours(events_today)

    tomorrow = 'tomorrow'
    time_min_2, time_max_2 = generate_timeMin_timeMax(tomorrow)
    events_tomorrow = get_events_from_calendar(service, CALENDAR_ID, time_min_2, time_max_2)
    available_hours_2 = generate_tomorrow_available_hours(events_tomorrow)

    today = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))

    return render_template('calendar.html', title='Calendar', available_hours=available_hours,
                           available_hours_2=available_hours_2, today=today, tomorrow=tomorrow)


@main.route("/new-event", methods=['GET', 'POST'])
def event():
    service = srv

    event_date = session['event_date']
    event_time = session['event_time']

    if 'login' in session:
        name = session['login']
    else:
        name = 'Enter your name here.'

    if 'email' in session:
        email = session['email']
    else:
        email = 'Enter your email here.'

    if request.method == 'POST':
        name = request.form['name']
        mail = request.form['email']
        title = request.form['m_title']

        new_event = build_event(name, mail, title, event_time, event_date)

        if 'gmail' in mail:
            add_event = service.events().insert(calendarId=CALENDAR_ID, body=new_event, sendUpdates="all",
                                                conferenceDataVersion=1).execute()
        else:
            add_event = service.events().insert(calendarId=CALENDAR_ID, body=new_event,
                                                conferenceDataVersion=1).execute()

        send_confirmation(mail, title, event_date, event_time)

        db_event_body = {
                'recipient': name,
                'recipient_mail': mail,
                'title': title,
                'event_date': event_date,
                'event_time': event_time,
                'event_datetime': event_date + ' ' + event_time
            }

        checkbox_data = request.form.get('remind')

        if checkbox_data:
            db_event_body['reminded'] = False
        else:
            db_event_body['reminded'] = True

        db.calendar.events.insert_one(db_event_body)

        clear_session()

        return redirect(url_for('main.calendar'))

    return render_template('event.html', title='Make an appointment', e_date=event_date, e_time=event_time, name=name,
                           email=email, client_id=gh_client_id)


@main.route("/github-authorized")
def github_authorized():
    if 'event_date' not in session:
        flash('Sorry, something went wrong. Please try again.', 'danger')
        return redirect(url_for('main.calendar'))

    if 'event_time' not in session:
        flash('Sorry, something went wrong. Please try again.', 'danger')
        return redirect(url_for('main.calendar'))

    session['code'] = request.args['code']
    flash('Thank you for logging with GitHub', 'success')
    url = f'https://github.com/login/oauth/access_token?client_id={gh_client_id}&client_secret={gh_client_secret}' \
          f'&code={session["code"]}'
    response = requests.get(url, allow_redirects=True)
    response_in_str = str(response.content, 'utf-8')
    access_token = get_access_token(response_in_str)
    github = Github(access_token)
    user = github.get_user()
    session['login'] = user.login
    if user.email:
        session['email'] = user.email
    session.pop('code', None)
    return redirect(url_for('main.event'))


@main.route("/login")
def login():
    session['event_date'] = request.args['event_date']
    session['event_time'] = request.args['event_time']
    return render_template('login.html')


@main.route("/login-with-github")
def login_with_github():
    url = f"https://github.com/login/oauth/authorize?scope=read:user&client_id={gh_client_id}"
    return redirect(url)


@main.route("/login-with-google")
def login_with_google():
    if 'event_date' not in session:
        flash('Sorry, something went wrong. Please try again.', 'danger')
        return redirect(url_for('main.calendar'))

    if 'event_time' not in session:
        flash('Sorry, something went wrong. Please try again.', 'danger')
        return redirect(url_for('main.calendar'))

    scopes = 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'
    flow = Flow.from_client_secrets_file('credentials.json', scopes,
                                         redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_url, _ = flow.authorization_url(prompt='consent')

    return render_template('auth-google.html', url=auth_url)


@main.route("/authorize-google", methods=['POST'])
def auth_with_google():
    scopes = 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'
    flow = Flow.from_client_secrets_file('credentials.json', scopes,
                                         redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    code = request.form['auth-google']
    flow.fetch_token(code=code)
    google_session = flow.authorized_session()
    user_info = google_session.get('https://www.googleapis.com/userinfo/v2/me').json()
    session['email'] = user_info['email']

    return redirect(url_for('main.event'))
