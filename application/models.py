from .database import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.column(db.String(), unique=True, nullable=False)
    username = db.column(db.String(), unique=True, nullable=False)
    password = db.column(db.String(), unique=True, nullable=False)
    type = db.column(db.String(), unique=True, nullable=False)


