from flask import Flask, render_template, redirect, request, url_for, flash, session, get_flashed_messages
from flask import current_app as app
from sqlalchemy import or_, and_
from .models import *
from datetime import datetime, timedelta

# ---------------------------------------------------------
# SLOT RANGE DEFINER AND FUNCTION
# ---------------------------------------------------------

SLOT_RANGES = {
    "morning": ("08:00", "12:00"),   # 8 AM - 12 PM
    "evening": ("16:00", "21:00"),   # 4 PM - 9 PM
}


def validate_future_slot(date_str, slot_key):
    SLOT_RANGES = {
        "morning": ("08:00", "12:00"),   # 8 AM – 12 PM
        "evening": ("16:00", "21:00"),   # 4 PM – 9 PM
    }

    if slot_key not in SLOT_RANGES:
        return False

    # parse date (YYYY-MM-DD)
    y, m, d = map(int, date_str.split("-"))

    # slot end time
    end_hh, end_mm = map(int, SLOT_RANGES[slot_key][1].split(":"))

    # selected slot end datetime
    slot_end = datetime(y, m, d, end_hh, end_mm)

    # current time (local machine time — works perfectly)
    now = datetime.now()

    return slot_end > now



# ---------------------------------------------------------
# HELPER FUNCTIONS
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

# NEW ENQUIRY - LANDING PAGE
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
                flash("Your enquiry has been received! Our team will contact you soon.", "success")
    # Redirect back to the homepage (or wherever the form is located)
    return redirect(url_for('homepage'))

# endpoints for departments
@app.route("/department/<string:dept_name>")
def department_page(dept_name):
    user_id = session.get("user_id")
    this_user = User.query.get(user_id)
    dept = Department.query.filter_by(name=dept_name).first()
    if not dept:
        flash("Department not found!", "danger")
        return redirect("/patient")
    
    # Get ALL doctors in this department - who arent blacklisted
    doctors = [
    d for d in Doctor.query.filter_by(department_id=dept.id).all()
    if d.user.blocked == False]

    return render_template("department_page.html", department=dept, doctors=doctors, this_user = this_user)


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

        if this_user.type == "admin":
            return redirect("/admin")
        elif this_user.type == "doctor":
            return redirect("/doctor")
        else:
            return redirect("/patient")  

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
        upcoming = Appointment.query.join(Patient).join(Doctor).filter(Appointment.status == "Upcoming").all()
        completed = Appointment.query.filter_by(status="Completed").all()

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
            Appointment.status == "Upcoming",
            or_(Patient.name.ilike(like), Doctor.doctor_name.ilike(like), Doctor.email.ilike(like))
        ).all()

        completed = Appointment.query.filter(
            Appointment.status == "Completed",
            or_(Patient.name.ilike(like), Doctor.doctor_name.ilike(like), Doctor.email.ilike(like))
        ).all()


    this_user = User.query.filter_by(type="admin").first()

    # === DASHBOARD STATS ===
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.filter_by(status="Upcoming").count()
    total_completed = Appointment.query.filter_by(status="Completed").count()


    return render_template("admin_dash.html",
        this_user=this_user,
        doctors=doctors,
        patients=patients,
        q=q,
        blacklisted_patients=blacklisted_patients,
        blacklisted_doctors=blacklisted_doctors,
        upcoming=upcoming,
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_completed=total_completed,
        completed = completed)


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

    appointments = Appointment.query.filter_by(doctor_id=doctor.id,status="Upcoming").all()

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

    appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status != "Cancelled"
    ).all()


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

        new_name = request.form.get("name")
        new_email = request.form.get("email")
        new_age = request.form.get("age")
        new_gender = request.form.get("gender")
        new_phone = request.form.get("phone")
        
        # Update patient table
        patient.name = request.form.get("name")
        patient.email = request.form.get("email")
        patient.age = request.form.get("age")
        patient.gender = request.form.get("gender")
        patient.phone = request.form.get("phone")

        # Update user table
        user = User.query.get(patient.user_id)
        user.username = new_name

        db.session.commit()
        flash("Patient updated successfully!", "success")
        return redirect("/admin")

    return render_template("edit_patient.html", patient=patient, this_user=current_user())


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
# VIEW DOCTOR DETAILS FROM PATIENT -- DEPARTMENTS
# ---------------------------------------------------------

@app.route("/doctor/details/<int:id>")
def doctor_details(id):
    patient, err = require_patient()
    if err:
        return err  

    doctor = Doctor.query.get_or_404(id)

    return render_template(
        "doctor_details.html",
        doctor=doctor,
        this_user=current_user()
    )


# ---------------------------------------------------------
# DOCTOR CRUD (Admin)
# ---------------------------------------------------------

@app.route("/edit_doctor/<int:id>", methods=['GET','POST'])
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    departments = Department.query.all()

    if request.method == "POST":
        new_name = request.form.get("doctor_name")
        new_email = request.form.get("email")
        new_exp = request.form.get("experience")
        new_dept = request.form.get("department_id")
        new_pass = request.form.get("password")

        doctor.doctor_name = request.form.get("doctor_name")
        doctor.email = request.form.get("email")
        doctor.experience = request.form.get("experience")
        doctor.department_id = request.form.get("department_id")

        # Update USER table also
        user = User.query.get(doctor.user_id)
        user.username = new_name
        if new_pass.strip():
            doctor.password = new_pass
            user.password = new_pass 

        db.session.commit()
        flash("Doctor updated successfully!", "success")
        return redirect("/admin")

    return render_template("edit_doctor.html",
        doctor=doctor, departments=departments)



@app.route('/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    active_app = Appointment.query.filter_by(doctor_id = doctor.id, status = "Upcoming").all()

    # Check if doctor has any appointments
    if active_app:
        flash("Cannot delete doctor. They still have appointments assigned.", "danger")
        return redirect('/admin')

    # Delete user account linked to doctor
    user = User.query.get(doctor.user_id)

    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()

    flash("Doctor deleted successfully!", "success")
    return redirect('/admin')




@app.route("/blacklist_doctor/<int:id>")
def blacklist_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    user = User.query.get(doctor.user_id)

    # Has upcoming appt??
    active_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status="Upcoming"
    ).all()

    if active_appointments:
        flash("Cannot blacklist doctor — they still have upcoming appointments!", "danger")
        return redirect("/admin")

    # Else, blacklist
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

    patient_id = request.args.get("id")

    # ADMIN & DOCTOR CAN VIEW ANY PATIENT BY ID
    if patient_id and user.type in ["admin", "doctor"]:
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

    # PATIENT CAN VIEW THEIR OWN HISTOYR
    if user.type == "patient":
        patient = Patient.query.filter_by(user_id=user.id).first_or_404()

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

    flash("Unauthorized!", "danger")
    return redirect("/")




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
            username = f"{username}"

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
    if err: 
        return err

    if request.method == "POST":
        date = request.form["date"]
        slot = request.form["slot"]

        # check if the slot has expired
        if not validate_future_slot(date, slot):
            flash("You cannot set availability for a past time or expired slot!", "danger")
            return redirect("/doctor/set_availability")

        existing = Availability.query.filter_by(
            doctor_id=doctor.id, date=date, slot=slot
        ).first()

        if existing:
            existing.is_available = True
        else:
            db.session.add(Availability(
                doctor_id=doctor.id,
                date=date,
                slot=slot,
                is_available=True
            ))

        db.session.commit()
        flash("Availability saved!", "success")
        return redirect("/doctor/set_availability")

    slots = Availability.query.filter_by(doctor_id=doctor.id).all()

    return render_template(
        "doctor_set_availability.html",
        doctor=doctor,
        next_days=next_7_days(),
        slots=slots
    )




# ---------------------------------------------------------
# PATIENT CHECK DOCTOR AVAILABILITY
# ---------------------------------------------------------

@app.route("/doctor/check_availability/<int:doctor_id>")
def patient_check_availability(doctor_id):
    doctor_obj = Doctor.query.get_or_404(doctor_id)

    slots = Availability.query.filter_by(doctor_id=doctor_obj.id).all()

    valid_slots = {}
    for s in slots:
        if validate_future_slot(s.date, s.slot) and s.is_available:
            valid_slots[f"{s.date}|{s.slot}"] = s

    return render_template(
        "patient_check_availability.html",
        doctor=doctor_obj,
        next_days=next_7_days(),
        slots_map=valid_slots,
        this_user=current_user()
    )




# ---------------------------------------------------------
# BOOK SLOT (PATIENT)
# ---------------------------------------------------------

@app.route("/book_slot/<int:slot_id>", methods=['POST'])
def book_slot(slot_id):
    patient, err = require_patient()
    if err: 
        return err

    slot = Availability.query.get_or_404(slot_id)

    # Check if this slot is expired
    if not validate_future_slot(slot.date, slot.slot):
        flash("This slot has already expired. Please select another.", "danger")
        return redirect("/patient")

    # Prevent double-booking same date+time
    existing = Appointment.query.filter_by(
        patient_id=patient.id,
        date=slot.date,
        time=slot.slot,
        status = "Upcoming"
    ).first()

    if existing:
        flash("You already have an appointment at this time!", "danger")
        return redirect("/patient")

    # Mark slot as unavailable
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
    
    appt.status = "Cancelled"

    slot = Availability.query.filter_by(
        doctor_id=appt.doctor_id, date=appt.date, slot=appt.time
    ).first()

    if slot:
        slot.is_available = True

    # db.session.delete(appt)
    db.session.commit()

    flash("Appointment cancelled!", "danger")
    return redirect("/patient")


# ---------------------------------------------------------
# RESCHEDULE APPOINTMENT (Patient)
# ---------------------------------------------------------

@app.route("/reschedule_appointment/<int:id>", methods=['GET', 'POST'])
def reschedule_appointment(id):
    patient, err = require_patient()
    if err: return err

    appt = Appointment.query.get_or_404(id)

    # Patient authorization check
    if appt.patient_id != patient.id:
        flash("Unauthorized!", "danger")
        return redirect("/patient")

    doctor = appt.doctor

    # Fetch doctor availability
    slots = Availability.query.filter_by(doctor_id=doctor.id, is_available=True).all()

    if request.method == "POST":
        new_slot_id = request.form.get("slot_id")
        if not new_slot_id:
            flash("Please select a valid slot.", "danger")
            return redirect(request.url)

        new_slot = Availability.query.get_or_404(new_slot_id)

        # Prevent past booking
        if not validate_future_slot(new_slot.date, new_slot.slot):
            flash("You cannot book a past or expired slot!", "danger")
            return redirect(request.url)

        # Free old slot
        old_slot = Availability.query.filter_by(
            doctor_id=doctor.id, date=appt.date, slot=appt.time
        ).first()
        if old_slot:
            old_slot.is_available = True

        # Occupy new slot
        new_slot.is_available = False

        # Update appointment
        appt.date = new_slot.date
        appt.time = new_slot.slot

        db.session.commit()

        flash("Appointment rescheduled successfully!", "success")
        return redirect("/patient")

    # GET → show form
    return render_template(
        "reschedule_appointment.html",
        appointment=appt,
        doctor=doctor,
        slots=slots,
        patient=patient,
        this_user=current_user()
    )




# ---------------------------------------------------------
# APPOINTMENT CRUD (Doctor)
# ---------------------------------------------------------


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
        time=appt.time,
        visit_type=appt.visit_type or "Completed"
    )
    db.session.add(treatment)

    slot = Availability.query.filter_by(
        doctor_id=doctor.id, date=appt.date, slot=appt.time
    ).first()
    if slot:
        slot.is_available = True

    # mark appointment completed instead of deleting as deleting can make a sequence of errors
    appt.status = "Completed"

    db.session.commit()

    flash("Appointment completed!", "warning")
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

    flash("Appointment deleted!", "danger")
    return redirect("/doctor")



@app.route("/update_appointment/<int:appointment_id>", methods=['GET', 'POST'])
def update_appointment(appointment_id):
    doctor, err = require_doctor()
    if err:
        return err

    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != doctor.id:
        flash("Unauthorized!", "danger")
        return redirect("/doctor")

    patient = appt.patient   # to show patient name in form

    if request.method == "POST":

        visit_type = request.form.get("visit_type")
        diagnosis = request.form.get("diagnosis")
        tests_done = request.form.get("tests_done")
        prescription = request.form.get("prescription")
        medicines = request.form.get("medicines")

        new_treatment = Treatment(
            appointment_id=appt.id,
            doctor_id=doctor.id,
            date=appt.date,
            time=appt.time,
            visit_type=visit_type,
            diagnosis=diagnosis,
            tests_done=tests_done,
            prescription=prescription,
            medicines=medicines
        )

        db.session.add(new_treatment)
        db.session.commit()  


        flash("Updated Successfully!", "success")
        return redirect("/doctor")

    return render_template("update_patient_history.html", appointment=appt, patient=patient)


