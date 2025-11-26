from flask import Flask, render_template, redirect, request, url_for, flash, session, get_flashed_messages
from flask import current_app as app
from sqlalchemy import or_, and_
from .models import *
from datetime import datetime, timedelta


# ---------------------------------------------------------
# 🔥 HELPER UTILS (replace 200 lines of repeated code)
# ---------------------------------------------------------

def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def require_login():
    user = current_user()
    return user if user else redirect("/login")


def require_doctor():
    user = current_user()
    if not user:
        return None, redirect("/login")

    doctor = Doctor.query.filter_by(user_id=user.id).first()
    if not doctor:
        flash("Unauthorized!", "danger")
        return None, redirect("/doctor")

    return doctor, None


def require_patient():
    user = current_user()
    if not user:
        return None, redirect("/login")

    patient = Patient.query.filter_by(user_id=user.id).first()
    if not patient:
        flash("Unauthorized!", "danger")
        return None, redirect("/patient")

    return patient, None


def next_7_days():
    today = datetime.today()
    return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]



# ---------------------------------------------------------
# ROUTES START
# ---------------------------------------------------------

@app.route("/", methods=['GET', 'POST'])
def homepage():
    return render_template("landing.html")



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        this_user = User.query.filter_by(username=username).first()

        if not this_user:
            return render_template("not_exists.html")

        if this_user.password != password:
            return render_template("incorrect_p.html")

        session["user_id"] = this_user.id

        # block checks
        if this_user.type == "patient":
            patient = Patient.query.filter_by(user_id=this_user.id).first()
            if patient and patient.blocked:
                flash("Your account has been blacklisted by the admin!", "danger")
                return redirect("/login")

        if this_user.type == "doctor" and this_user.blocked:
            flash("Your account has been blacklisted by the admin!", "danger")
            return redirect("/login")

        # redirects
        if this_user.type == "admin":
            return redirect("/admin")
        elif this_user.type == "doctor":
            return redirect("/doctor")
        else:
            return render_template("patient_dash.html", username=username, this_user=this_user)

    return render_template("login.html")



@app.route("/logout")
def logout():
    get_flashed_messages()
    session.clear()
    return redirect("/login")



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method=="POST":
        username = request.form.get("username")
        password = request.form.get("password")

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        age = request.form.get("age")
        gender = request.form.get("gender")

        if User.query.filter_by(username=username).first():
            return render_template("already_exists.html")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        new_patient = Patient(user_id=new_user.id, name=name, age=age, email=email, gender=gender, phone=phone)
        db.session.add(new_patient)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")



# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

@app.route("/admin")
def admin_dash():
    q = request.args.get("q", "").strip()

    if q == "":
        doctors = Doctor.query.join(User).filter(User.blocked == False).all()
        blacklisted_doctors = Doctor.query.join(User).filter(User.blocked == True).all()
        patients = Patient.query.filter_by(blocked=False).all()
        blacklisted_patients = Patient.query.filter_by(blocked=True).all()
        upcoming = Appointment.query.join(Patient).join(Doctor).all()

    else:
        like = f"%{q}%"
        doctors = Doctor.query.filter(
            or_(Doctor.doctor_name.ilike(like), Doctor.email.ilike(like))
        ).all()

        patients = Patient.query.filter(
            Patient.blocked == False,
            or_(Patient.name.ilike(like), Patient.email.ilike(like), Patient.phone.ilike(like))
        ).all()

        blacklisted_patients = Patient.query.filter_by(blocked=True).all()

        blacklisted_doctors = Doctor.query.join(User).filter(
            User.blocked == True,
            or_(Doctor.doctor_name.ilike(like), Doctor.email.ilike(like))
        ).all()

        upcoming = Appointment.query.join(Patient).join(Doctor).filter(
            or_(Patient.name.ilike(like), Doctor.doctor_name.ilike(like), Doctor.email.ilike(like))
        ).all()

    this_user = User.query.filter_by(type="admin").first()

    return render_template("admin_dash.html",
        this_user=this_user,
        doctors=doctors,
        patients=patients,
        q=q,
        blacklisted_patients=blacklisted_patients,
        blacklisted_doctors=blacklisted_doctors,
        upcoming=upcoming)



# ---------------------------------------------------------
# DOCTOR DASHBOARD
# ---------------------------------------------------------

@app.route("/doctor")
def doctor_dash():
    user = require_login()
    doctor = Doctor.query.filter_by(user_id=user.id).first()

    if not doctor:
        flash("Doctor profile not found!", "danger")
        return redirect("/login")

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patients = {a.patient for a in appointments}

    return render_template("doctor_dash.html",
        doctor=doctor, this_user=user, appointments=appointments, patients=patients)



# ---------------------------------------------------------
# PATIENT DASHBOARD
# ---------------------------------------------------------

@app.route("/patient")
def patient_dash():
    patient, err = require_patient()
    if err: return err

    appointments = Appointment.query.filter_by(patient_id=patient.id).all()

    return render_template("patient_dash.html",
        this_user=current_user(),
        patient=patient,
        appointments=appointments)



# ---------------------------------------------------------
# EDIT PROFILE (Patient)
# ---------------------------------------------------------

@app.route("/edit_profile", methods=['GET','POST'])
def edit_profile():
    patient, err = require_patient()
    if err: return err

    this_user = current_user()

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

    return render_template("patient_edit_profile.html",
        patient=patient, this_user=this_user)



# ---------------------------------------------------------
# PATIENT CRUD FROM ADMIN
# ---------------------------------------------------------

@app.route("/delete_patient/<int:id>")
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    user = User.query.get(patient.user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Patient deleted successfully!", "success")
    return redirect("/admin")


@app.route("/edit_patient/<int:id>", methods=['GET','POST'])
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

    return render_template("edit_patient.html", patient=patient)


@app.route("/blacklist_patient/<int:id>")
def blacklist_patient(id):
    patient = Patient.query.get_or_404(id)
    patient.blocked = True
    db.session.commit()
    flash("Patient blacklisted!", "danger")
    return redirect("/admin")


@app.route("/unblacklist_patient/<int:id>")
def unblacklist_patient(id):
    patient = Patient.query.get_or_404(id)
    patient.blocked = False
    db.session.commit()
    flash("Patient unblacklisted!", "success")
    return redirect("/admin")



# ---------------------------------------------------------
# DOCTOR CRUD (Admin)
# ---------------------------------------------------------

@app.route("/edit_doctor/<int:id>", methods=['GET','POST'])
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    departments = Department.query.all()

    if request.method == "POST":
        doctor.doctor_name = request.form.get("doctor_name")
        doctor.email = request.form.get("email")
        doctor.experience = request.form.get("experience")
        doctor.department_id = request.form.get("department_id")

        new_pass = request.form.get("password")
        if new_pass.strip():
            doctor.password = new_pass

        db.session.commit()
        flash("Doctor updated successfully!", "success")
        return redirect("/admin")

    return render_template("edit_doctor.html",
        doctor=doctor, departments=departments)



@app.route("/delete_doctor/<int:id>")
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    flash("Doctor deleted!", "danger")
    return redirect("/admin")


@app.route("/blacklist_doctor/<int:id>")
def blacklist_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    user = User.query.get(doctor.user_id)
    user.blocked = True
    db.session.commit()
    flash("Doctor blacklisted!", "warning")
    return redirect("/admin")


@app.route("/unblacklist_doctor/<int:id>")
def unblacklist_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    user = User.query.get(doctor.user_id)
    user.blocked = False
    db.session.commit()
    flash("Doctor unblacklisted!", "success")
    return redirect("/admin")



# ---------------------------------------------------------
# PATIENT HISTORY PAGE
# ---------------------------------------------------------

@app.route("/patient_history")
def patient_history():
    user = current_user()
    if not user:
        return redirect("/login")

    # -----------------------------
    # ADMIN VIEWING A PATIENT
    # -----------------------------
    patient_id = request.args.get("id")
    if patient_id and user.type == "admin":
        patient = Patient.query.get_or_404(patient_id)

        appointments = Appointment.query.filter_by(patient_id=patient.id).all()
        treatments = Treatment.query.join(Appointment).filter(
            Appointment.patient_id == patient.id
        ).all()

        return render_template(
            "patient_history.html",
            this_user=user,
            patient=patient,
            appointments=appointments,
            treatments=treatments
        )

    # -----------------------------
    # NORMAL PATIENT VIEWING THEMSELVES
    # -----------------------------
    patient = Patient.query.filter_by(user_id=user.id).first()
    if not patient:
        flash("Unauthorized!", "danger")
        return redirect("/")

    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == patient.id
    ).all()

    return render_template(
        "patient_history.html",
        this_user=user,
        patient=patient,
        appointments=appointments,
        treatments=treatments
    )



# ---------------------------------------------------------
# ADD NEW DOCTOR (ADMIN)
# ---------------------------------------------------------

@app.route("/add_doctor", methods=['GET','POST'])
def add_doctor():
    if request.method=="POST":
        username = request.form.get("username")
        phone = request.form.get("phone")
        email = request.form.get("email")
        department_name = request.form.get("department")
        experience = request.form.get("experience")
        password = request.form.get("password")

        if not username.lower().startswith("dr."):
            username = f"Dr. {username}"

        if Doctor.query.filter_by(doctor_name=username).first():
            flash("Doctor already exists!", "danger")
            return redirect("/add_doctor")

        new_user = User(username=username, password=password, type="doctor")
        db.session.add(new_user)
        db.session.commit()

        department = Department.query.filter_by(name=department_name).first()
        if not department:
            department = Department(name=department_name, description="No description provided")
            db.session.add(department)
            db.session.commit()

        doctor = Doctor(
            doctor_name=username,
            department=department,
            password=password,
            email=email,
            user_id=new_user.id,
            type="doctor",
            department_id=department.id,
            experience=experience,
        )
        db.session.add(doctor)
        db.session.commit()

        flash(f"🎉 Doctor {username} added successfully!", "success")
        return redirect("/admin")

    return render_template("add_new_doc.html")



# ---------------------------------------------------------
# DOCTOR AVAILABILITY
# ---------------------------------------------------------

@app.route("/doctor/availability", methods=["GET","POST"])
def doctor_availability():
    doctor, err = require_doctor()
    if err: return err

    if request.method == "POST":
        date = request.form.get("date")
        slot = request.form.get("slot")

        new_availability = Availability(doctor_id=doctor.id, date=date, slot=slot)
        db.session.add(new_availability)
        db.session.commit()
        flash("Availability added!", "success")

    slots = Availability.query.filter_by(doctor_id=doctor.id).all()

    return render_template("doctor_availability.html",
        doctor=doctor,
        slots=slots,
        next_7_days=next_7_days())



@app.route("/doctor/availability/delete/<int:id>")
def delete_availability(id):
    slot = Availability.query.get(id)
    if slot:
        db.session.delete(slot)
        db.session.commit()
        flash("Availability removed!", "success")
    return redirect("/doctor/availability")



@app.route("/doctor/set_availability", methods=['GET','POST'])
def doctor_set_availability():
    doctor, err = require_doctor()
    if err: return err

    if request.method == "POST":
        date = request.form["date"]
        slot = request.form["slot"]

        existing = Availability.query.filter_by(
            doctor_id=doctor.id, date=date, slot=slot
        ).first()

        if existing:
            existing.is_available = True
        else:
            db.session.add(Availability(
                doctor_id=doctor.id, date=date, slot=slot, is_available=True
            ))

        db.session.commit()
        flash("Availability saved!", "success")
        return redirect("/doctor/set_availability")

    slots = Availability.query.filter_by(doctor_id=doctor.id).all()

    return render_template("doctor_set_availability.html",
        doctor=doctor, next_days=next_7_days(), slots=slots)



# ---------------------------------------------------------
# PATIENT CHECK DOCTOR AVAILABILITY
# ---------------------------------------------------------

@app.route("/doctor/check_availability/<int:doctor_id>")
def patient_check_availability(doctor_id):
    doctor_obj = Doctor.query.get_or_404(doctor_id)

    slots = Availability.query.filter_by(doctor_id=doctor_obj.id).all()
    slots_map = {f"{s.date}|{s.slot}": s for s in slots}

    return render_template("patient_check_availability.html",
        doctor=doctor_obj,
        next_days=next_7_days(),
        slots_map=slots_map,
        this_user=current_user())



# ---------------------------------------------------------
# BOOK SLOT (PATIENT)
# ---------------------------------------------------------

@app.route("/book_slot/<int:slot_id>", methods=['POST'])
def book_slot(slot_id):
    patient, err = require_patient()
    if err: return err

    slot = Availability.query.get_or_404(slot_id)
    slot.is_available = False

    new_appt = Appointment(
        patient_id=patient.id,
        doctor_id=slot.doctor_id,
        date=slot.date,
        time=slot.slot
    )

    db.session.add(new_appt)
    db.session.commit()

    flash("Slot booked successfully!", "success")
    return redirect("/patient")



# ---------------------------------------------------------
# CLEAR AVAILABILITY (Doctor)
# ---------------------------------------------------------

@app.route("/doctor/clear_availability")
def clear_availability():
    doctor, err = require_doctor()
    if err: return err

    Availability.query.filter_by(doctor_id=doctor.id).delete()
    db.session.commit()

    flash("All availability cleared!", "success")
    return redirect("/doctor/set_availability")



# ---------------------------------------------------------
# CANCEL APPOINTMENT (Patient)
# ---------------------------------------------------------

@app.route("/cancel_appointment/<int:id>")
def cancel_appointment(id):
    patient, err = require_patient()
    if err: return err

    appt = Appointment.query.get_or_404(id)

    if appt.patient_id != patient.id:
        flash("Unauthorized!", "danger")
        return redirect("/patient")

    slot = Availability.query.filter_by(
        doctor_id=appt.doctor_id, date=appt.date, slot=appt.time
    ).first()

    if slot:
        slot.is_available = True

    db.session.delete(appt)
    db.session.commit()

    flash("Appointment cancelled!", "success")
    return redirect("/patient")



# ---------------------------------------------------------
# APPOINTMENT CRUD (Doctor)
# ---------------------------------------------------------

@app.route("/edit_appointment/<int:appointment_id>", methods=['GET','POST'])
def edit_appointment(appointment_id):
    doctor, err = require_doctor()
    if err: return err

    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != doctor.id:
        flash("Unauthorized!", "danger")
        return redirect("/doctor")

    if request.method == "POST":
        new_date = request.form.get("date")
        new_time = request.form.get("time")

        old_slot = Availability.query.filter_by(
            doctor_id=doctor.id, date=appt.date, slot=appt.time
        ).first()
        if old_slot: old_slot.is_available = True

        new_slot = Availability.query.filter_by(
            doctor_id=doctor.id, date=new_date, slot=new_time
        ).first()

        if not new_slot:
            flash("Slot does not exist!", "danger")
            return redirect(request.referrer)

        if not new_slot.is_available:
            flash("Slot is already booked!", "danger")
            return redirect(request.referrer)

        new_slot.is_available = False

        appt.date = new_date
        appt.time = new_time
        db.session.commit()

        flash("Appointment updated!", "success")
        return redirect("/doctor")

    return render_template("edit_appointment.html",
        appointment=appt, doctor=doctor)



@app.route("/complete_appointment/<int:appointment_id>")
def complete_appointment(appointment_id):
    doctor, err = require_doctor()
    if err: return err

    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != doctor.id:
        flash("Unauthorized!", "danger")
        return redirect("/doctor")

    treatment = Treatment(
        appointment_id=appt.id,
        doctor_id=doctor.id,
        date=appt.date,
        time=appt.time
    )
    db.session.add(treatment)

    slot = Availability.query.filter_by(
        doctor_id=doctor.id, date=appt.date, slot=appt.time
    ).first()
    if slot: slot.is_available = True

    db.session.delete(appt)
    db.session.commit()

    flash("Appointment completed!", "success")
    return redirect("/doctor")



@app.route("/delete_appointment/<int:appointment_id>")
def delete_appointment(appointment_id):
    doctor, err = require_doctor()
    if err: return err

    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != doctor.id:
        flash("Unauthorized!", "danger")
        return redirect("/doctor")

    slot = Availability.query.filter_by(
        doctor_id=doctor.id, date=appt.date, slot=appt.time
    ).first()
    if slot: slot.is_available = True

    db.session.delete(appt)
    db.session.commit()

    flash("Appointment deleted!", "success")
    return redirect("/doctor")



@app.route("/record_visit/<int:appointment_id>", methods=['GET','POST'])
def record_visit(appointment_id):
    doctor, err = require_doctor()
    if err: return err

    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != doctor.id:
        flash("Unauthorized!", "danger")
        return redirect("/doctor")

    if request.method == "POST":
        t = Treatment(
            appointment_id=appt.id,
            doctor_id=doctor.id,
            date=appt.date,
            time=appt.time
        )
        db.session.add(t)

        slot = Availability.query.filter_by(
            doctor_id=doctor.id, date=appt.date, slot=appt.time
        ).first()
        if slot: slot.is_available = True

        db.session.delete(appt)
        db.session.commit()

        flash("Visit recorded!", "success")
        return redirect("/doctor")

    return render_template("record_visit.html",
        appointment=appt, patient=appt.patient, doctor=doctor)

