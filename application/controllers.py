from flask import Flask, render_template, redirect, request
from flask import current_app as app # it refers to the app.py

from .models import User, Info, db

@app.route("/", methods=['GET', 'POST'])
def homepage():
    return render_template("landing.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username= request.form.get("username")
        password= request.form.get("password")
        this_user= User.query.filter_by(username=username).first()
        if this_user:
            if this_user.password == password:
                if this_user.type == "admin":
                    return render_template("/admin")
                else:
                    return render_template("patient_dash.html")
            else:
                return render_template("incorrect_p.html")
        return render_template("login.html")
    
