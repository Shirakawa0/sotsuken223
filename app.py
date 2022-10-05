from flask import Flask, render_template, request,redirect,url_for,session
import random, string
from db.db_manager import db_manager

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

@app.route("/")
def u_login_page():
    return render_template("u_login.html")

@app.route("/u_signup")
def u_signup_page():
    return render_template("u_signup_1.html")

@app.route("/u_signup",methods=["POST"])
def u_signup():
    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    dep = request.form.get("dep")
    grade = request.form.get("grade")
    Class = request.form.get("class") # 区別のためcは大文字

    
    
    param = (id,pw,name,dep,grade,Class)
    dbmg = db_manager()

    return render_template("u_signup_3.html")

@app.route("/home")
def u_home_page():
    if "id" not in session:
        return redirect("/")

    return render_template("u_home.html")

@app.route("/u_add")
def u_add_page():
    return render_template("u_add_1.html")

@app.route("/u_modify")
def u_modify_page():
    return render_template("u_modify_1.html")

@app.route("/u_modify/confirm", methods=["POST"])
def u_modify_confirm():
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    schedule = {"step":step,"detail":detail,"place":place,"date_time":date_time}

    return render_template("u_modify_2",schedule=schedule)

@app.route("/u_modify/done")
def u_modify():
    id = session["id"]
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    dbmg = db_manager()

    return render_template("u_modify_3.html")

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