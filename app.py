#pip freeze > requirements.txt

from requests_oauthlib import OAuth2Session
import requests
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow_sqlalchemy import ModelSchema
from flask_cors import CORS, cross_origin
import os
from .config import *
from datetime import datetime

app = Flask(__name__, instance_relative_config=True)
cors = CORS(app, support_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config.from_object(DevelopmentConfig())
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
app.development = True
app.secret_key = app.config['SECRET_KEY']

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

@app.route("/login")
@cross_origin(supports_credentials=True)
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    fitbit = OAuth2Session(app.config['CLIENT_ID'],
        redirect_uri=app.config['CALLBACK_URL'],
        scope=scope
        )

    authorization_url, state = fitbit.authorization_url(
        app.config['AUTHORIZATION_BASE_URL'],
    )
    
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state

    return redirect("authorization_url")

@app.route('/callback', methods=["GET"])
@cross_origin(supports_credentials=True)
def callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    fitbit = OAuth2Session(app.config['CLIENT_ID'],
        redirect_uri=app.config['CALLBACK_URL'],  
        state=session['oauth_state'],
        )
    token = fitbit.fetch_token(app.config['TOKEN_URL'], 
        client_secret=app.config['CLIENT_SECRET'],
        authorization_response=request.url,
        )
    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('about'))

@app.route("/about", methods=["GET"])
@cross_origin(supports_credentials=True)
def about():
    """Fetching a protected resource using an OAuth 2 token.
    """
    print("token: ", session['oauth_token'])
    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=session['oauth_token'])
    profile_url = 'https://api.fitbit.com/1/user/-/profile.json'
    steps_url = 'https://api.fitbit.com/1/user/-/activities/steps/date/today/7d.json'
    activities_url = 'https://api.fitbit.com/1/user/-/activities/date/today/1m.json'
    
    profile = fitbit.get(profile_url)
    steps = fitbit.get(steps_url)
    activities = fitbit.get(activities_url)

    print(activities.json())

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
    summary = jsonify(summary)
    return redirect('http://localhost:3000')#summary

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
    calendar = ["Sun", "Mon", "Tues", "Wed", "Thurs", "Fri", "Sat"]
    for day in activity_data['activities-steps']:
        steps.append(
            {
                "day": calendar[datetime.strptime(day['dateTime'], "%Y-%m-%d").weekday()],
                "date": day['dateTime'], 
                "steps": int(day['value'])
            }
        )
        total_steps += int(day['value'])
    return steps, total_steps


if __name__ == '__main__':
    app.run(debug=True)
