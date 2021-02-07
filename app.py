#pip freeze > requirements.txt

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('becca-runs.config')
app.config.from_pyfile('becca-runs.instance.config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)

from app import routes, models
