from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
import random, string
from db.db_manager import db_manager

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

@app.route("/")
def u_login_page():
    return render_template("u_login.html")

@app.route("/", methods=["POST"])
def u_login():
    id = request.form.get("id")
    pw = request.form.get("pw")
    
    dbmg = db_manager()
    sql = "select * from u_account where id=%s"
    result = dbmg.exec_query(sql, id)

    hash_pw, _ = dbmg.calc_pw_hash(pw, result[0]["salt"])

    if hash_pw == result[0]["hash_pw"]:
        session["id"] = result[0]["id"]
        session["user_name"] = result[0]["name"]
        # sessionの有効期限
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        return redirect("/home")
    else:
        return redirect("/") 


@app.route("/u_signup")
def u_signup_page():
    return render_template("u_signup_1.html")

@app.route("/u_signup", methods=["POST"])
def u_signup():
    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    dep = request.form.get("dep")
    grade = request.form.get("grade")
    Class = request.form.get("class") # 区別のためcは大文字

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    class_id = dep + grade + Class

    dbmg.exec_query("insert into u_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,class_id))

    return render_template("u_signup_3.html")

@app.route("/home")
def u_home_page():
    if "id" not in session:
        return redirect("/")

    return render_template("u_home.html")

@app.route("/u_add")
def u_add_page():
    return render_template("u_add_1.html")

@app.route("/u_add/u_add2",methods=["POST"])
def u_add_confirm():
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    result = (company,step,detail,place,date_time)
    return render_template("u_add_2.html",result=result)

@app.route("/u_add/u_add2/u_add3",methods=["POST"])
def u_add():
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")
    print(date_time)

    dbmg = db_manager()
    dbmg.exec_query("insert into schedule values(%s,%s,%s,%s,%s,%s)",(session["id"],company,date_time,step,detail,place))
    return render_template("u_add_3.html")

@app.route("/u_register")
def u_register_page():
    return render_template("u_register_1.html")

@app.route("/u_register/u_register2",methods=["POST"])
def u_register_confirm():
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    result = (company,step,detail,place,date_time)
    return render_template("u_register_2.html",result=result)

@app.route("/u_register/u_register2/u_register3",methods=["POST"])
def u_register():
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")
    print(date_time)

    dbmg = db_manager()
    dbmg.exec_query("insert into schedule values(%s,%s,%s,%s,%s,%s)",(session["id"],company,date_time,step,detail,place))
    return render_template("u_register_3.html")

if __name__ == "__main__":
    app.run(debug=True)