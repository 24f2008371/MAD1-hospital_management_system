from flask import Flask
from application.database import db #3 database
from application.models import *

app = None

def create_app():
    app = Flask(__name__)
    app.debug = True 
    # All changes will be incorporated while app is running and shows errors
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.sqlite3" # 3 database
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Tracks Changes
    db.init_app(app) # 3 database 
    app.app_context().push() # runtime error if not using this, brings everything under context of flask app

    with app.app_context():
        db.create_all()

app = create_app()
from application.controllers import * #2 controllers  

if __name__ == "__main__":
    app.run() 





