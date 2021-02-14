#pip freeze > requirements.txt

from requests_oauthlib import OAuth2Session
import requests
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow_sqlalchemy import ModelSchema
from flask_cors import CORS
import os
from .config import *
from datetime import datetime

calendar = ["Sun", "Mon", "Tues", "Wed", "Thurs", "Fri", "Sat"]

app = Flask(__name__, instance_relative_config=True)

app.config.from_object(DevelopmentConfig())
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
app.development = True
app.secret_key = app.config['SECRET_KEY']

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

scope = app.config["SCOPE"]

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)

class UserSchema(ModelSchema):
     class Meta:
        model = User

@app.route("/hello", methods=['GET', 'POST'])
def users():
    return "hello"

@app.route("/")
def homepage():
    return "Becca Runs"

@app.route("/login")
def login():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    fitbit = OAuth2Session(app.config['CLIENT_ID'],
        redirect_uri=app.config['CALLBACK_URL'],
        scope=scope
        )

    authorization_url, state = fitbit.authorization_url(
        app.config['AUTHORIZATION_BASE_URL'], prompt="login"
    )
    
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state

    return redirect(authorization_url)

@app.route('/oauth_callback', methods=["GET"])
def oauth_callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    fitbit = OAuth2Session(app.config['CLIENT_ID'],
        redirect_uri=app.config['CALLBACK_URL'],  
        state=session['oauth_state']
        )

    token = fitbit.fetch_token(app.config['TOKEN_URL'], 
        client_secret=app.config['CLIENT_SECRET'],
        authorization_response=request.url,
        )
    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=token)
    profile_url = 'https://api.fitbit.com/1/user/-/profile.json'
    profile = fitbit.get(profile_url)
    name = profile.json()["user"]["fullName"].split(' ')[0].lower()

    # print('\n*********************')
    # print('token:', token['user_id'])
    # print('*********************\n')


    url = f"http://localhost:3000/loggedin/{name}"

    return redirect(url)
    #return redirect(url_for('.about'))

@app.route("/steps", methods=["GET"])
def calculate_steps():
    # data = [
    #     {'x': 1, 'y': 8},
    #     {'x': 2, 'y': 5},
    #     {'x': 3, 'y': 4},
    #     {'x': 4, 'y': 9},
    #     {'x': 5, 'y': 2},
    #     {'x': 6, 'y': 3},
    #     {'x': 7, 'y': 2},
    #     {'x': 8, 'y': 9},
    #     ]
    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=session['oauth_token'])
    steps_url = f'https://api.fitbit.com/1/user/-/activities/steps/date/today/3m.json'
    steps = fitbit.get(steps_url)
    [steps, total_steps] = step_summary(steps.json())

    data = steps

    return jsonify(data)


@app.route("/summary", methods=["GET"])
def about():
    """Fetching a protected resource using an OAuth 2 token.
    """
    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=session['oauth_token'])
    profile_url = 'https://api.fitbit.com/1/user/-/profile.json'
    steps_url = 'https://api.fitbit.com/1/user/-/activities/steps/date/today/1y.json'
    activities_url = 'https://api.fitbit.com/1/user/-/activities/date/today/1m.json'
    
    profile = fitbit.get(profile_url)
    steps = fitbit.get(steps_url)
    activities = fitbit.get(activities_url)

    badges = badge_summary(profile.json()["user"])
    [steps, total_steps] = step_summary(steps.json())

    summary = {
        "Name": profile.json()["user"]["fullName"],
        "Age": profile.json()["user"]["age"],
        "Badges": badges,
        "Total Steps This Week": total_steps,
        "Steps by Day": steps,
        "activities": activities.json()

    }

    #requests.get("http://localhost:3000/about")
    print('\n*********************')
    print(jsonify(steps))
    print('*********************\n')

    return jsonify(steps)

@app.route("/current_user")
def current_user():
    token = session["oauth_token"]
    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=session["oauth_token"])
    profile_url = 'https://api.fitbit.com/1/user/-/profile.json'
    profile = fitbit.get(profile_url)
    # print('\n*********************')
    # print(profile.json())
    # print('*********************\n')
    name = profile.json()["user"]["fullName"].split(' ')[0].lower()
    return jsonify({'name': name, 'user_id': token['user_id']})

@app.route("/logout")
def logout():
    session["oauth_token"] = ''
    session["oauth_state"] = ''
    # print('\n*********************')
    # print("session: ", session)
    # print('*********************\n')
    return {'name': ''}#redirect('http://localhost:3000/home')
    

def badge_summary(user_data):
    badges = []
    for badge in user_data["topBadges"]:
        badges.append({
            "Date": badge["dateTime"],
            "Achievement": badge["earnedMessage"]
            })
    return badges


def step_summary(activity_data):
    steps = []
    total_steps = 0
    for day in activity_data['activities-steps']:
        steps.append(
            {
                #"day": calendar[datetime.strptime(day['dateTime'], "%Y-%m-%d").weekday()],
                "x": day['dateTime'], #date
                "y": int(day['value']) #steps
            }
        )
        total_steps += int(day['value'])
    return steps, total_steps


if __name__ == '__main__':
    app.run(debug=True)
