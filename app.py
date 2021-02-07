#pip freeze > requirements.txt

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema
from flask_cors import CORS

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('becca-runs.config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
#ma = Marshmallow(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    location = db.Column(db.String(128))

class UserSchema(ModelSchema):
     class Meta:
        model = User

@app.route("/users", methods=['GET', 'POST'])
def users():
    if methods 

if __name__ == '__main__':
    app.run(debug=True)
