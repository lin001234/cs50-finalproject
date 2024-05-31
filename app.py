import os

import sqlite3
from flask import Flask, flash, redirect, render_template, jsonify, request, session # type: ignore
from flask_session import Session # type: ignore
from werkzeug.security import check_password_hash, generate_password_hash #type: ignore
from datetime import datetime, timedelta


#configure app
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    #Forget any user_id
    session.clear()

    if request.method == "POST":
        #if no username submitted
        if not request.form.get("username"):
            return ("Input username", 401)
        #if no password submitted
        elif not request.form.get("password"):
            return ("Input password", 401)
        #connect to sqlite
        conn = sqlite3.connect("app.db")
        #create cursor object using cusor() method
        db = conn.cursor()
        #query database for username
        db.execute(
            "SELECT * FROM users WHERE username = (?)", [request.form.get("username")]
        )
        rows = db.fetchall()
        #ensure username exist and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return ("Invalid username and/or password", 401)
        
        #remember which user logged in
        session["user_id"] = rows[0][0]
        conn.close()
        #redirect user to home page
        return redirect("/")
    
    #user reached route via GET
    else:
        return render_template("login.html")
    
@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        #if no username submitted
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("password1")
        for row in rows:
            if row[1] == username:
                return ("Username take", 401)
        if not request.form.get("username"):
            return ("Input username", 401)
        #if no password submitted
        elif not request.form.get("password"):
            return ("Input password", 401)
        elif not request.form.get("password1"):
            return ("Confirm password", 401)
        elif password != confirmation:
            return("Passwords do not match", 401)
        else:
            hashcode = generate_password_hash(password,method='pbkdf2',salt_length=32)
            conn = sqlite3.connect('app.db', timeout=10)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, hash) VALUES(?,?)", (request.form.get("username"), hashcode))
            conn.commit()
            cur.close()
            conn.close()
            return render_template("login.html")
        
    else:
        return render_template("register.html")
@app.route("/change_pass", methods = ["GET", "POST"] )
def change_pass():
    if request.method == "POST":
        old_pass = request.form.get("old_pass")
        new_pass = request.form.get("new_pass")
        confirm_pass = request.form.get("password1")
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", str(session["user_id"]))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if old_pass == "" or new_pass == "" or confirm_pass == "":
            return ("MISSING PASSWORDS", 401)
        elif new_pass != confirm_pass:
            return ("New passwords do not match", 401)
        elif not check_password_hash(rows[0][2], old_pass):
            return("INCORRECT PASSWORD",401)
        else:
            hashcode = generate_password_hash(new_pass,method='pbkdf2',salt_length=32)
            conn = sqlite3.connect('app.db', timeout=10)
            cur = conn.cursor()
            cur.execute("UPDATE users SET hash = ? WHERE id = ?", (hashcode, str(session["user_id"])))
            conn.commit()
            cur.close()
            conn.close()
            return redirect("/")
    else:
        return render_template("change_pass.html")








app.config['expiration_time'] = datetime.now() + timedelta(hours = 0,minutes=10)
remaining_time = app.config['expiration_time'] - datetime.now()

def get_remaining_time_in_seconds():
    remaining_time = app.config['expiration_time'] - datetime.now()
    remaining_time_in_seconds = remaining_time.total_seconds()
    return remaining_time_in_seconds

@app.route("/remaining_time")
def remaining_time():
    remaining_time_in_seconds = get_remaining_time_in_seconds()
    return jsonify({'remaining_time_in_seconds': remaining_time_in_seconds})


@app.route('/reset', methods=['POST'])
def reset():
    if request.method == 'POST':
        app.config['expiration_time'] = datetime.now() + timedelta(hours= 0 ,minutes=0)
        return render_template('set_timer.html')

@app.route('/timer', methods=['POST','GET'])
def timer():
    if request.method == 'POST':
        hours = int(request.form.get("hours"))
        minutes = int(request.form.get("minutes"))
        if hours=="" or minutes=="":
            return("ENTER HOURS OR MINUTES")
        elif minutes >= 60:
            return("ENTER UP TO 60 MINUTES")
        total_seconds = hours*60*60 + minutes*60
        today_date = datetime.now()
        date = today_date.date()
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("INSERT INTO focus (user_id,hours,minutes,date) VALUES(?,?,?,?)", (str(session["user_id"]),hours, minutes, date))
        conn.commit()
        cur.close()
        db = conn.cursor()
        db.execute("SELECT * FROM focus WHERE user_id =? AND hours = ? AND minutes=? AND date=?", (str(session["user_id"]),hours, minutes, date))
        row = db.fetchall()
        timer_id = row[0][0]
        db.close()
        conn.close()
        app.config['expiration_time'] = datetime.now() + timedelta(hours= hours ,minutes=minutes)
        return render_template('focus.html', timer_id=timer_id, total_seconds=total_seconds)
    else:
        return render_template("set_timer.html")
    

@app.route('/history', methods=["POST","GET"])
def history():

    conn = sqlite3.connect('app.db', timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT * FROM focus WHERE user_id = ? ORDER BY date DESC", (str(session["user_id"])))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        date = row[3]
        hours =row[1]
        minutes=row[2]
    return render_template("history.html", rows=rows)


@app.route('/stop', methods = ["POST"])
def stop():
    if request.method == "POST":
        timer_id = int(request.form.get("timer_id"))
        if not request.form.get("timer_id"):
            return ("insert timer_id")

        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("DELETE FROM focus WHERE id = ?", [str(timer_id)])
        conn.commit()
        cur.close()
        conn.close()
        return render_template("set_timer.html")
    
@app.route('/delete_history', methods=["POST"])
def delete_history():
    if request.method =="POST":
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("DELETE FROM focus WHERE user_id = ?", [str(session["user_id"])])
        conn.commit()
        cur.close()
        conn.close()
        return render_template("history.html")    






@app.route("/todo", methods=["GET", "POST"])
def todo():
    if request.method=="POST":
        inputdate = request.form.get("date")
        list = request.form.get("todo")
        if not request.form.get("date"):
            return("Enter the date")
        elif not request.form.get("todo"):
            return("Enter the work to be done")
        date = datetime.strptime(inputdate, "%Y-%m-%d")
        present = datetime.now()
        if date.date() < present.date():
            return("Date entered should not be before today.")
        else:
            conn = sqlite3.connect('app.db', timeout=10)
            cur = conn.cursor()
            db = conn.cursor()
            cs = conn.cursor()
            cur.execute("INSERT INTO todo (id,date,list) VALUES(?,?,?)",  (str(session["user_id"]),inputdate,list ))
            db.execute("SELECT * FROM users WHERE id = ? ", (str(session["user_id"])))
            cs.execute("SELECT * FROM todo WHERE id = ? ORDER BY date" , (str(session["user_id"])))
            conn.commit()
            user = db.fetchall()
            rows = cs.fetchall()
            cur.close()
            db.close()
            cs.close()
            conn.close()
            for row in rows:
                dates = row[1]
                todolist = row[2]
            return render_template("todo.html",user=user, rows=rows)
    else:
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM todo WHERE id = ? ORDER BY date", (str(session["user_id"])))
        rows = cur.fetchall()
        cur.close()
        db = conn.cursor()
        db.execute("SELECT * FROM users WHERE id = ?", (str(session["user_id"])))
        user = db.fetchall()
        db.close()
        conn.close()
        for row in rows:
            dates = row[1]
            todolist = row[2]
        return render_template("todo.html", rows = rows, user=user)

@app.route("/delete_todo", methods= ["GET", "POST"]) 
def delete_todo():
    if request.method == "POST":
        date = request.form.get("delete_row")
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("DELETE FROM todo WHERE id = ? AND date = ?", (str(session["user_id"]), date))
        conn.commit()
        cur.close()
        db = conn.cursor()
        db.execute("SELECT * FROM todo WHERE id = ? ORDER BY date", (str(session["user_id"])))
        rows = db.fetchall()
        db.close()
        cs = conn.cursor()
        cs.execute("SELECT * FROM users WHERE id = ?", (str(session["user_id"])))
        user = cs.fetchall()
        db.close()
        conn.close()
        for row in rows:
            dates= row[1]
            todolist =row[2]
        return render_template("todo.html", rows = rows, user=user)
    else:
        conn = sqlite3.connect('app.db', timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM todo WHERE id = ? ORDER BY date", (str(session["user_id"])))
        rows = cur.fetchall()
        cur.close()
        db = conn.cursor()
        db.execute("SELECT * FROM users WHERE id = ?", (str(session["user_id"])))
        user = db.fetchall()
        db.close()
        conn.close()
        for row in rows:
            dates = row[1]
            todolist = row[2]
        return render_template("todo.html", rows = rows, user=user)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")