from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import secrets

#Miten poistaa subject? silloin sen subjectin threadsit ja messaget ei saa näkyä
#lisää delete subject admin oikeuksilla

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")
app.admin = getenv("ADMIN_PASS")
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"].lower()
    password = request.form["password"]
    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        return render_template("error.html", message=f"Käyttäjätiliä {username} ei löydy!")
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        else:
            return render_template("error.html", message="Salasana on väärä!")

@app.route("/register", methods=["POST"])
def register():
    admin = False
    username = request.form["username"].lower()
    password = request.form["password1"]
    password2 = request.form["password2"]
    adminrights = request.form["admin"]
    if adminrights != "NONE" and adminrights != app.admin:
        return render_template("error.html", message="Admin salasana oli väärä! Rekisteröidy uudestaan")
    if password != password2:
        return render_template("error.html", message="Salasanat eivät täsmää.")
    if adminrights == app.admin:
        admin = True
    sqlusers = text("SELECT count(username) FROM users WHERE username=:username")
    vastaus = db.session.execute(sqlusers, {"username":username})
    if vastaus.fetchone()[0] == 0:
        hash_value = generate_password_hash(password)
        sql = text("INSERT INTO users (username, password, admin) VALUES (:username, :password, :admin)")
        db.session.execute(sql, {"username":username, "password":hash_value, "admin":admin})
        db.session.commit()
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        return render_template("error.html", message="Käyttäjätunnus on jo käytössä.")

def isadmin():
    user = session["username"]
    sql = text("SELECT admin FROM users WHERE username = :user")
    admin = db.session.execute(sql, {"user":user}).fetchone()[0]
    return admin

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/logout")
def logout():
    del session["username"]
    del session["csrf_token"]
    return redirect("/")

@app.route("/error")
def error():
    return render_template("error.html")

@app.route("/frontpage")
def frontpage():
    ''' OBS.
    Variable "sql" underneath is choosing every subject name, subject id, creator, sum of unique threads,
    sum of messages + last sent message from a table that contains every message,
    with it's thread name and subject name.
    First we SELECT a table like this:
    subject name    subject id      creator         thread name             message                                 timestamp
    kekkonen        1               jorma34         silmälasit              "Minkä merkkiset?"                      2022-12-12 16:00:01
    formula 1       2               seppo1          renkaat                 "Millaiset renkaat Kimillä on?"         2022-12-12 16:10:01
    kekkonen        1               jorma34         presidentti             "Mikä teki hänestä Suomen parhaimman?"  2023-12-12 16:23:21

    From this table we select every subject name with its creator, sum of unique thread names and sum of messages + last sent
    messages. This table is stored in variable "sql".
    '''
    sql = text('''SELECT info.sub AS subject, info.subid AS subjectid, info.uname AS creator, count(DISTINCT info.thr) AS threadsum, 
    count(info.mess) AS messagesum, MAX(info.time) AS lastsent FROM 
    (SELECT s.id AS subid, u.username AS uname, s.content AS sub, 
    t.content as thr, m.content as mess, m.created_at AS time FROM subjects s 
    JOIN users u ON s.user_id = u.id AND s.visible = TRUE AND s.secret = FALSE
    LEFT JOIN threads t ON s.id = t.subject_id AND t.visible = TRUE 
    LEFT JOIN messages m ON m.thread_id = t.id AND m.visible = TRUE 
    GROUP BY s.id, u.username, s.content, t.content, m.content, m.created_at ORDER BY s.content) AS info 
    GROUP BY info.sub, info.subid, info.uname ORDER BY info.sub''')

    cont = db.session.execute(sql).fetchall()
    return render_template("frontpage.html", content = cont)

@app.route("/subject/<int:subjectid>")
def subject(subjectid):
    #We want to find all subject's threads
    sql = text("SELECT t.id AS threadid, t.content AS threadname, u.username AS username FROM threads t, users u WHERE t.subject_id = :subjectid AND t.visible = TRUE AND u.id = t.user_id")
    cont = db.session.execute(sql, {"subjectid":subjectid}).fetchall()
    return render_template("subject.html", content = cont, subject_id = subjectid)

@app.route("/thread/<int:threadid>")
def thread(threadid):
    #We want to find all thread's messages
    sql = text("SELECT m.id AS messageid, m.content AS message, m.created_at AS time, u.username AS username FROM messages m, users u WHERE m.thread_id = :threadid AND m.user_id = u.id AND m.visible = TRUE ORDER BY m.created_at")
    cont = db.session.execute(sql, {"threadid":threadid}).fetchall()
    threadsql = text("SELECT t.content, u.username FROM threads t, users u WHERE t.id = :threadid AND t.user_id = u.id")
    threadname = db.session.execute(threadsql, {"threadid":threadid}).fetchone()
    return render_template("thread.html", content = cont, thread_id = threadid, question = threadname[0], creator = threadname[1])

@app.route("/add", methods=["POST"])
def add():
    check_csrf()
    level = request.form["level"]
    if level == "modify":
        time = datetime.now()
        tm = request.form["tm"]
        con = request.form["allcontent"] + f" (muokattu {time.strftime('%Y/%m/%d %H:%M:%S')})"
        id = request.form["id"]
        if tm == "t":
            sql = text("UPDATE threads SET content = :con WHERE id = :id")
            db.session.execute(sql, {"con": con, "id": id})
            db.session.commit()
            return redirect(f"/thread/{id}")
        elif tm == "m":
            sqltid = text("SELECT t.id FROM threads t, messages m WHERE t.id = m.thread_id AND m.id = :id")
            tid = db.session.execute(sqltid, {"id":id}).fetchone()[0]
            sql = text("UPDATE messages SET content = :con WHERE id = :id")
            db.session.execute(sql, {"con": con, "id": id})
            db.session.commit()
            return redirect(f"/thread/{tid}")

    content = request.form["content"]
    uname = request.form["uname"]
    idsql = text("SELECT id FROM users WHERE username = :uname")
    userid = db.session.execute(idsql, {"uname":uname}).fetchone()[0]
    if level == "subject":
        content = content.upper()
        search = text("SELECT id FROM subjects WHERE content = :content")
        if db.session.execute(search, {"content":content}).fetchone() == None:
            sql = text("INSERT INTO subjects (user_id, content) VALUES (:userid, :content)")
            db.session.execute(sql, {"userid":userid, "content":content})
            db.session.commit()
            return redirect("/frontpage")
        else:
            return render_template("error.html", message="Alue on jo olemassa tai se on piilotettu.")
    elif level == "thread":
        subject_id = request.form["sid"]
        sql = text("INSERT INTO threads (subject_id, user_id, content) VALUES (:subject_id, :userid, :content)")
        db.session.execute(sql, {"subject_id":subject_id, "userid":userid, "content":content})
        db.session.commit()
        return redirect(f"/subject/{subject_id}")
    elif level == "message":
        thread_id = request.form["tid"]
        timenow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = text("INSERT INTO messages (thread_id, user_id, created_at, content) VALUES (:thread_id, :userid, :timenow, :content)")
        db.session.execute(sql, {"thread_id":thread_id, "userid":userid, "timenow":timenow, "content":content})
        db.session.commit()
        return redirect(f"/thread/{thread_id}")

@app.route("/modify", methods=["POST"])
def modify():
    check_csrf()
    sessionuser = request.form["username"]
    createduser = request.form["creator"]
    level = request.form["level"]
    if sessionuser != createduser:
        return render_template("error.html", message="Et voi muokata ketjua, koska et ole luonut sitä.")
    elif sessionuser == createduser:
        if level == "T":
            threadid = request.form["thread"]
            sql = text("SELECT content FROM threads WHERE id = :threadid")
            threadname = db.session.execute(sql, {"threadid":threadid}).fetchone()[0]
            return render_template("textbox.html", tm="t", content=threadname, id=threadid, len=300)
        if level == "M":
            messageid = request.form["message"]
            sql = text("SELECT content FROM messages WHERE id = :messageid")
            messagename = db.session.execute(sql, {"messageid": messageid}).fetchone()[0]
            return render_template("textbox.html", tm="m", content=messagename, id=messageid, len=700)

@app.route("/delete", methods=["POST"])
def delete():
    check_csrf()
    admin = False
    level = request.form["level"]
    sessionuser = request.form["username"]
    createduser = request.form["creator"]
    sqladmin = text("SELECT admin FROM users WHERE username = :sessionuser")
    if db.session.execute(sqladmin, {"sessionuser":sessionuser}).fetchone()[0] == True:
        admin = True
    if sessionuser != createduser and admin == False:
        return render_template("error.html", message="Et voi poistaa ketjua, koska et ole luonut sitä etkä ole admin.")
    if level == "T":
        tid = request.form["thread"]
        sid = request.form["subject"]
        if sessionuser == createduser or admin == True:
            sql = text("UPDATE threads SET visible = FALSE WHERE id = :tid")
            db.session.execute(sql, {"tid":tid})
            db.session.commit()
            return redirect(f"/subject/{sid}")
    if level == "M":
        mid = request.form["message"]
        tid = request.form["thread"]
        if sessionuser == createduser or admin == True:
            sql = text("UPDATE messages SET visible = FALSE WHERE id = :mid")
            db.session.execute(sql, {"mid": mid})
            db.session.commit()
            return redirect(f"/thread/{tid}")

@app.route("/subjectdelete", methods=["POST"])
def subjectdelete():
    check_csrf()
    if isadmin():
        sname = request.form["subject"].upper()
        sql = text("SELECT id FROM subjects WHERE content = :sname")
        if str(db.session.execute(sql, {"sname":sname}).fetchall()) == "[]":
            return render_template("error.html", message="Kyseistä aluetta ei löytynyt")
        sql = text("UPDATE subjects SET visible = FALSE WHERE content = :sname")
        db.session.execute(sql, {"sname":sname})
        db.session.commit()
        return redirect("/frontpage")
    return render_template("error.html", message="Et ole admin!")

@app.route("/search", methods=["POST"])
def search():
    check_csrf()
    message = request.form["message"]
    if isadmin():
        sql = text('''SELECT DISTINCT t.id AS tid, t.content AS tname, s.content FROM threads t, messages m, subjects s WHERE 
        m.content ILIKE :message AND m.thread_id = t.id AND t.subject_id = s.id AND s.visible = TRUE AND t.visible = TRUE AND m.visible = TRUE AND s.secret = FALSE''')
        searching = db.session.execute(sql, {"message":f'%{message}%'}).fetchall()
        sqlsecret = text('''SELECT DISTINCT t.id AS tid, t.content AS tname, s.content FROM threads t, messages m, subjects s WHERE 
        m.content ILIKE :message AND m.thread_id = t.id AND t.subject_id = s.id AND s.visible = TRUE AND t.visible = TRUE AND m.visible = TRUE AND s.secret = TRUE''')
        secretsearching = db.session.execute(sqlsecret, {"message":f'%{message}%'}).fetchall()
        if str(searching) == "[]" and str(secretsearching) == "[]":
            return render_template("error.html", message="Hakusanalla ei löydy viestejä.")
        return render_template("search.html", content=searching, secretcontent=secretsearching)
    else:
        user = session["username"]
        sqluserid = text("SELECT id FROM users WHERE username = :user")
        userid = db.session.execute(sqluserid, {"user": user}).fetchone()[0]
        sql = text('''SELECT DISTINCT t.id AS tid, t.content AS tname, s.content FROM threads t, messages m, subjects s WHERE 
        m.content ILIKE :message AND m.thread_id = t.id AND t.subject_id = s.id AND s.visible = TRUE AND t.visible = TRUE AND m.visible = TRUE AND s.secret = FALSE''')
        searching = db.session.execute(sql, {"message":f'%{message}%', "userid":userid}).fetchall()
        sqlsecret = text('''SELECT DISTINCT t.id AS tid, t.content AS tname FROM threads t
        JOIN users u ON t.user_id = u.id 
        JOIN messages m ON m.content ILIKE :message AND m.thread_id = t.id 
        JOIN subjects s ON t.subject_id = s.id AND s.visible = TRUE AND s.secret = TRUE
        JOIN secrets sec ON sec.subject_id = s.id AND sec.user_id = :userid''')
        secretsearching = db.session.execute(sqlsecret, {"message":f'%{message}%', "userid":userid}).fetchall()
        if str(searching) == "[]" and str(secretsearching) == "[]":
            return render_template("error.html", message="Hakusanalla ei löydy viestejä.")
        return render_template("search.html", content=searching, secretcontent=secretsearching)

@app.route("/addsecret", methods=["POST"])
def addsecret():
    check_csrf()
    if isadmin():
        user = session["username"]
        sqluserid = text("SELECT id FROM users WHERE username = :user")
        userid = db.session.execute(sqluserid, {"user":user}).fetchone()[0]
        subjectname = request.form["content"]
        subjectname = subjectname.upper()
        comp = text("SELECT content FROM subjects WHERE content = :subjectname")
        if str(db.session.execute(comp, {"subjectname":subjectname}).fetchall()) == "[]":
            sql = text("INSERT INTO subjects (user_id, content, secret) VALUES (:userid, :subjectname, 'True')")
            db.session.execute(sql, {"userid":userid, "subjectname":subjectname})
            db.session.commit()
            return redirect("/secretsubjects")
    return render_template("error.html", message="Et ole admin!")

@app.route("/newsecretmember", methods=["POST"])
def newsecretmember():
    check_csrf()
    if isadmin():
        useraddname = request.form["user"]
        subjectid = request.form["sid"]
        sqluser = text("SELECT id FROM users WHERE username = :useraddname")
        if str(db.session.execute(sqluser, {"useraddname":useraddname}).fetchall()) == "[]":
            return render_template("error.html", message="Ei löydy kyseistä käyttäjää.")
        userid = db.session.execute(sqluser, {"useraddname":useraddname}).fetchone()[0]
        sqlduplicates = text("SELECT id FROM secrets WHERE subject_id = :subjectid AND user_id = :userid")
        if db.session.execute(sqlduplicates, {"subjectid":subjectid, "userid":userid}).fetchone() == None:
            sqlsecret = text("INSERT INTO secrets (subject_id, user_id) VALUES (:subjectid, :userid)")
            db.session.execute(sqlsecret, {"subjectid": subjectid, "userid":userid})
            db.session.commit()
            return redirect("/secretsubjects")
        return render_template("error.html", message="Käyttäjä on jo salaisella alueella.")
    return render_template("error.html", message="Et voi lisätä käyttäjiä alueelle.")

@app.route("/secretsubjects")
def secretsubjects():
    if isadmin():
        sql = text('''SELECT info.sub AS subject, info.subid AS subjectid, info.uname AS creator, count(DISTINCT info.thr) AS threadsum, 
        count(info.mess) AS messagesum, MAX(info.time) AS lastsent FROM 
        (SELECT s.id AS subid, u.username AS uname, s.content AS sub, 
        t.content as thr, m.content as mess, m.created_at AS time FROM subjects s 
        JOIN users u ON s.user_id = u.id AND s.visible = TRUE AND s.secret = TRUE
        LEFT JOIN threads t ON s.id = t.subject_id AND t.visible = TRUE 
        LEFT JOIN messages m ON m.thread_id = t.id AND m.visible = TRUE 
        GROUP BY s.id, u.username, s.content, t.content, m.content, m.created_at ORDER BY s.content) AS info 
        GROUP BY info.sub, info.subid, info.uname ORDER BY info.sub''')
        content = db.session.execute(sql).fetchall()
        if str(content) == "[]":
            return render_template("secret.html", alert = "Ei salaisia keskustelualueita", content = "")
        return render_template("secret.html", content = content)
    else:
        user = session["username"]
        sqluserid = text("SELECT id FROM users WHERE username = :user")
        userid = db.session.execute(sqluserid, {"user":user}).fetchone()[0]
        sql = text('''SELECT info.sub AS subject, info.subid AS subjectid, info.uname AS creator, count(DISTINCT info.thr) AS threadsum, 
        count(info.mess) AS messagesum, MAX(info.time) AS lastsent FROM 
        (SELECT s.id AS subid, u.username AS uname, s.content AS sub, 
        t.content as thr, m.content as mess, m.created_at AS time FROM subjects s 
        JOIN users u ON s.user_id = u.id AND s.visible = TRUE AND s.secret = TRUE
        JOIN secrets sec ON sec.user_id = :userid AND sec.subject_id = s.id
        LEFT JOIN threads t ON s.id = t.subject_id AND t.visible = TRUE 
        LEFT JOIN messages m ON m.thread_id = t.id AND m.visible = TRUE 
        GROUP BY s.id, u.username, s.content, t.content, m.content, m.created_at ORDER BY s.content) AS info 
        GROUP BY info.sub, info.subid, info.uname ORDER BY info.sub''')
        content = db.session.execute(sql, {"userid":userid}).fetchall()
        if str(content) == "[]":
            return render_template("error.html", message = "Ei salaisia keskustelualueita.")
        return render_template("secret.html", content = content)

