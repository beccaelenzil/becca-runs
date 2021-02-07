#pip freeze > requirements.txt

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from oauth import OAuthSignIn
from .oauth_signin import OAuthSignIn


app = Flask(__name__, instance_relative_config=True)

app.config.from_object('becca-runs.config')
app.config['OAUTH_CREDENTIALS'] = {
    'fitbit': {
        'id': app.config['OAUTH_CLIENT_ID'],
        'secret': app.config['FITBIT_API_KEY']
    },
}


db = SQLAlchemy(app)
migrate = Migrate(app, db)

fitbit = oauth.remote_app('fitbit',
    base_url='',
    request_token_url='',
    access_token_url='',
    authorize_url='',
    consumer_key='',
    consumer_secret=''
)

lm = LoginManager(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

class UserSchema(ModelSchema):
     class Meta:
        model = User

friendship_table = Table('association', Base.metadata,
    Column('user1_id', Integer, ForeignKey('user.id')),
    Column('user2_id', Integer, ForeignKey('user.id'))
)

@app.route("/users", methods=['GET', 'POST'])
def users():
    return "hello, world"

@app.route('/oauth_callback')
def oauth_callback():
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider('fitbit')
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return "authenticaltion failed"
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
