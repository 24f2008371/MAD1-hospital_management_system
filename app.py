from flask import Flask
from application.database import db #3 database
from application.models import *
from flask_login import LoginManager

app = None

def create_app():
    app = Flask(__name__)
    # set a secret key to use flash() and sessions
    app.secret_key = 'hello'
    app.debug = True 
    # All changes will be incorporated while app is running and shows errors
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.sqlite3" # 3 database
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Tracks Changes

    login_manager = LoginManager() 
    login_manager.init_app(app)
    login_manager.login_view = 'login' # type of url for


    @login_manager.user_loader # the user id 
    def load_user(user_id):
        return User.query.get(int(user_id))

    db.init_app(app) # 3 database 
    app.app_context().push() # runtime error if not using this, brings everything under context of flask app
    return app

app = create_app()
from application.controllers import * #2 controllers  


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            user1 = User(username = 'admin', password = '1234', type = 'admin')
            db.session.add(user1)
            db.session.commit()
            print("Database created and admin user added!")
        else:
            print("Database already exists.")
    app.run() 





