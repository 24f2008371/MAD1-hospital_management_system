from flask import Flask, render_template, redirect, request
from flask import current_app as app # it refers to the app.py

from .models import User, db

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

@app.route("/patient")
def patient_dash():
    this_user = User.query.filter_by(type="patient").first()
    return render_template("patient_dash.html", this_user = this_user)