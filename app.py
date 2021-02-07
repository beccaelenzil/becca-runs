#pip freeze > requirements.txt

from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow_sqlalchemy import ModelSchema
from flask_cors import CORS
import os
from .config import *


app = Flask(__name__, instance_relative_config=True)

app.config.from_object(DevelopmentConfig())
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
app.development = True
app.secret_key = app.config['SECRET_KEY']

db = SQLAlchemy(app)
migrate = Migrate(app, db)

scope = ["activity", "heartrate", "location", "nutrition","sleep","social","weight"]

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
@app.route("/login")
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

    return redirect(authorization_url)


    #https://www.fitbit.com/oauth2/authorize?
    #response_type=code
    #&client_id=22942C
    #&redirect_uri=https%3A%2F%2Fexample.com%2Ffitbit_auth
    #&scope=activity%20nutrition%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight

@app.route('/callback', methods=["GET"])
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


    return redirect(url_for('.profile'))

@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    print("token: ", session['oauth_token'])
    fitbit = OAuth2Session(app.config['CLIENT_ID'], token=session['oauth_token'])
    print("fitbit request: ", fitbit)
    return {"authenticated": "yes!"}


if __name__ == '__main__':
    app.run(debug=True)
