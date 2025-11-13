from flask import Flask, render_template, redirect, request, url_for, flash
from flask import current_app as app # it refers to the app.py

from .models import *

@app.route("/", methods=['GET', 'POST'])
def homepage():
    return render_template("landing.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username= request.form.get("username")
        password= request.form.get("password")
        this_user= User.query.filter_by(username=username).first()
        if this_user: # if this user exists
            if this_user.password == password:
                if this_user.type == "admin":
                    return redirect("/admin")
                elif this_user.type == "doctor":
                    return redirect("/doctor")
                else:
                    return render_template("patient_dash.html", username=username,this_user=this_user)
            else:
                return render_template("incorrect_p.html")
        else:
            return render_template("not_exists.html")   
    return render_template("login.html")
    
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method=="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        this_user = User.query.filter_by(username=username).first()
        if this_user: # if this user exists
            return render_template("already_exists.html")
        else: # if this user does not exist
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
        return redirect("/login")
    return render_template("register.html")

# endpoint for admin dashboard

@app.route("/admin")
def admin_dash():
    this_user = User.query.filter_by(type="admin").first()
    return render_template("admin_dash.html", this_user = this_user)

@app.route("/doctor")
def doctor_dash():
    this_user = User.query.filter_by(type="doctor").first()
    return render_template("doctor_dash.html", this_user = this_user)

@app.route("/patient")
def patient_dash():
    this_user = User.query.filter_by(type="patient").first()
    return render_template("patient_dash.html", this_user = this_user)

@app.route("/patient_history")
def patient_history():
    this_user = User.query.filter_by(type="patient").first()
    return render_template("patient_history.html", this_user = this_user)

# ADD DOCTOR ENDPOINT
@app.route("/add_doctor", methods=['GET', 'POST'])
def add_doctor():
    if request.method=="POST":
        username = request.form.get("username")
        # doctor_name = request.form.get("doctor_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        department = request.form.get("department")
        name= request.form.get("name")
        experience = request.form.get("experience")
        description = request.form.get("description")
        password = request.form.get("password")
        availability = request.form.get("availability")

        if not username.lower().startswith("dr."):
            username = f"Dr. {username}"
            
        this_user = Doctor.query.filter_by(doctor_name=username).first()
        if this_user:
            return render_template("already_exists.html")
        else:
            new_user = User(username=username, password=password, type="doctor")
            db.session.add(new_user)
            db.session.commit()

            department_name = department
            department = Department.query.filter_by(name=name).first()
            if not department:
                department = Department(
                    name=name,
                    description = description
                )
                db.session.add(department)
                db.session.commit()

            doctor = Doctor(
                doctor_name = username,
                department = department,
                password = password,
                email = email,
                user_id = new_user.id,
                type="doctor",
                department_id = department.id,
                experience = experience,
            )
            db.session.add(doctor)
            db.session.commit()

            flash(f"🎉 Doctor {username} added successfully to the system!", "success")
            return redirect("/admin")
    return render_template("add_new_doc.html")

# endpoints for departments
@app.route("/cardiology")
def cardiology():
    return render_template("cardiology.html")
@app.route("/neurology")
def neurology():
    return render_template("neurology.html")
@app.route("/oncology")
def oncology():
    return render_template("oncology.html")
@app.route("/general")
def general():
    return render_template("general.html")


# --- NEW ENQUIRY SUBMISSION ENDPOINT ---
@app.route("/submit_enquiry", methods=['POST'])
def submit_enquiry():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if name and email and message:
                # Create a new Enquiry object and save it in the database
                new_enquiry = Enquiry(name=name, email=email, message=message)
                db.session.add(new_enquiry)
                db.session.commit()
    # Redirect back to the homepage (or wherever the form is located)
    return redirect(url_for('homepage'))

