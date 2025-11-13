from .database import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key = True)
    blocked = db.Column(db.Boolean(), default=False, nullable=False)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(), default="patient", nullable=False)
    patient = db.relationship('Patient', backref='user', cascade="all, delete-orphan")
    doctor = db.relationship('Doctor', backref='user', cascade="all, delete-orphan")

class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer(),primary_key = True)
    doctor_name = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    department_id = db.Column(db.Integer(), db.ForeignKey('department.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    experience = db.Column(db.Integer(), nullable=False)
    appointment = db.relationship('Appointment', backref='doctor', cascade="all, delete-orphan")


class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer(),primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer(), nullable=False)
    gender = db.Column(db.String(), nullable=False)
    phone = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    appointment = db.relationship('Appointment', backref='patient', cascade="all, delete-orphan")

class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer(),primary_key = True)
    name = db.Column(db.String())
    description = db.Column(db.String())
    doctor = db.relationship('Doctor', backref='department')

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer(),primary_key = True)
    patient_id = db.Column(db.Integer(), db.ForeignKey('patient.id', ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer(), db.ForeignKey('doctor.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.String(), nullable=False)
    time = db.Column(db.String(), nullable=False)
    
class Treatment(db.Model):
    __tablename__ = 'treatment'
    id = db.Column(db.Integer(),primary_key = True)
    appointment_id = db.Column(db.Integer(), db.ForeignKey('appointment.id', ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer(), db.ForeignKey('doctor.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.String(), nullable=False)
    time = db.Column(db.String(), nullable=False)
    appointment = db.relationship('Appointment', backref='treatment')

class Enquiry(db.Model):
    __tablename__ = 'enquiry'
    id = db.Column(db.Integer(),primary_key = True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    message = db.Column(db.String(), nullable=False)