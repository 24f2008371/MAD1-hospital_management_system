from flask import Flask, render_template, redirect, request, url_for, flash
from flask import current_app as app # it refers to the app.py
from sqlalchemy import or_
from flask import session

from .models import *

@app.route("/", methods=['GET', 'POST'])
def homepage():
    return render_template("landing.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        this_user = User.query.filter_by(username=username).first()

        if this_user:
            if this_user.password == password:

                session["user_id"] = this_user.id

                # BLOCK CHECK FOR PATIENT
                if this_user.type == "patient":
                    patient = Patient.query.filter_by(user_id=this_user.id).first()
                    if patient and patient.blocked:
                        flash("Your account has been blacklisted by the admin!", "danger")
                        return redirect("/login")

                # BLOCK CHECK FOR DOCTOR  ⭐ FIX HERE ⭐
                if this_user.type == "doctor":
                    if this_user.blocked:
                        flash("Your account has been blacklisted by the admin!", "danger")
                        return redirect("/login")

                # NORMAL LOGIN FLOW
                if this_user.type == "admin":
                    return redirect("/admin")
                elif this_user.type == "doctor":
                    return redirect("/doctor")
                else:
                    return render_template("patient_dash.html", username=username, this_user=this_user)

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

        # Fields for patient table
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        age = request.form.get("age")
        gender = request.form.get("gender")

        this_user = User.query.filter_by(username=username).first()
        if this_user: # if this user exists
            return render_template("already_exists.html")
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        new_patient = Patient(user_id = new_user.id, name=name, age=age, email=email, gender=gender, phone=phone)
        db.session.add(new_patient)
        db.session.commit()

        return redirect("/login")
    return render_template("register.html")



# endpoint for admin dashboard
@app.route("/admin")
def admin_dash():

    # Search query
    q = request.args.get("q", "").strip()

    # Show normal data if search is empty
    if q == "":
        doctors = Doctor.query.join(User).filter(User.blocked == False).all()
        blacklisted_doctors = Doctor.query.join(User).filter(User.blocked == True).all()
        patients = Patient.query.filter_by(blocked=False).all()
        blacklisted_patients = Patient.query.filter_by(blocked = True).all()

    else:
        ilike_q = f"%{q}%" # f-string 
        
        # in SQL %Ridhi% means jahan bhi Ridhi aaye ____Ridhi_____ 

        # or_(...) → SQLAlchemy function jo OR condition banata hai (ya to ye condition ya vo).

        doctors = Doctor.query.filter(
            or_(
                Doctor.doctor_name.ilike(ilike_q), # ilike is the case insensitive version of LIKE function of SQL
                Doctor.email.ilike(ilike_q)
            )
        ).all()

        patients = Patient.query.filter_by(blocked=False).filter(
            or_(
                Patient.name.ilike(ilike_q),
                Patient.email.ilike(ilike_q),
                Patient.phone.ilike(ilike_q)
            )  
        ).all()

        blacklisted_patients = Patient.query.filter_by(blocked = True).all()


    this_user = User.query.filter_by(type="admin").first()
    return render_template("admin_dash.html", this_user = this_user, doctors = doctors, patients = patients, q=q, blacklisted_patients = blacklisted_patients, blacklisted_doctors = blacklisted_doctors)




@app.route("/doctor")
def doctor_dash():
    this_user = User.query.filter_by(type="doctor").first()
    return render_template("doctor_dash.html", this_user = this_user)




@app.route("/patient")
def patient_dash():
    this_user = User.query.filter_by(type="patient").first()
    return render_template("patient_dash.html", this_user = this_user)


# EDIT PATIENT PROFILE - ON PATIENT DASHBOARD
@app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():

    # Fetch logged-in user using session
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")  # if not logged in

    this_user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        patient.name = request.form.get("name")
        patient.email = request.form.get("email")
        patient.phone = request.form.get("phone")
        patient.age = request.form.get("age")
        patient.gender = request.form.get("gender")

        new_pass = request.form.get("password")
        if new_pass.strip():
            this_user.password = new_pass

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect("/patient")

    return render_template("patient_edit_profile.html", patient=patient, this_user=this_user)


# Delete patient route
@app.route("/delete_patient/<int:id>")
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    user = User.query.get(patient.user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Patient deleted successfully!", "success")
    return redirect("/admin")

# Edit patient route
@app.route("/edit_patient/<int:id>", methods = ['GET','POST'])
def edit_patient(id):
    patient = Patient.query.get_or_404(id)

    if request.method == "POST":
        patient.name = request.form.get("name")
        patient.email = request.form.get("email")
        patient.age = request.form.get("age")
        patient.gender = request.form.get("gender")
        patient.phone = request.form.get("phone")

        db.session.commit()

        flash("Patient updated successfully!", "success")
        return redirect("/admin")
    return render_template("edit_patient.html", patient = patient)


# Blacklist patient route
@app.route("/blacklist_patient/<int:id>")
def blacklist_patient(id):
    patient = Patient.query.get_or_404(id)

    patient.blocked = True
    db.session.commit()

    db.session.commit()

    flash("Patient has been blacklisted successfully!", "danger")
    return redirect("/admin")


# Unblacklist patient route
@app.route("/unblacklist_patient/<int:id>")
def unblacklist_patient(id):
    patient = Patient.query.get_or_404(id)
    patient.blocked = False
    db.session.commit()

    flash("Patient unblacklisted successfully!", "success")
    return redirect("/admin")


# Edit Doctor Route
@app.route("/edit_doctor/<int:id>", methods=["GET", "POST"])
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    # Load all departments for dropdown
    departments = Department.query.all()

    if request.method == "POST":
        doctor.doctor_name = request.form.get("doctor_name")
        doctor.email = request.form.get("email")
        doctor.experience = request.form.get("experience")

        # Department selection (stored as department_id)
        doctor.department_id = request.form.get("department_id")

        # Password update only if user entered something
        new_pass = request.form.get("password")
        if new_pass.strip() != "":
            doctor.password = new_pass

        db.session.commit()
        flash("Doctor details updated successfully!", "success")
        return redirect("/admin")

    return render_template("edit_doctor.html", doctor=doctor, departments=departments)



# Delete Doctor route
@app.route("/delete_doctor/<int:id>")
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor deleted successfully!", "danger")
    return redirect("/admin")


# Blacklist doctor route
@app.route("/blacklist_doctor/<int:id>")
def blacklist_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    user = User.query.get(doctor.user_id)
    user.blocked = True

    db.session.commit()
    flash("Doctor has been blacklisted!", "warning")
    return redirect("/admin")

# Unblacklist Doctor route
@app.route("/unblacklist_doctor/<int:id>")
def unblacklist_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    user = User.query.get(doctor.user_id)
    user.blocked = False

    db.session.commit()
    flash("Doctor unblacklisted successfully!", "success")
    return redirect("/admin")




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
            flash("Doctor already exists!", "danger")
            return redirect("/add_doctor")

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

