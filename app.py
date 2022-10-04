from flask import Flask, render_template, request,redirect,url_for
import random, string
from db.db_manager import db_manager

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

@app.route("/")
def u_login_page():
    return render_template("u_login.html")

@app.route("/",methods=["POST"])
def u_login():
    id = request.form.get("id")
    pw = request.form.get("pw")
    
    dbmg = db_manager.db_manager()
    sql = "select * from u_account where id=%s"
    result = dbmg.exec_query(sql, id)

    hash_pw, salt = dbmg.calc_pw_hash(pw, result[0]["salt"])

    print("hash_pw" + hash_pw)
    print("db_pw" + result[0]["hash_pw"])

    if hash_pw == result[0]["hash_pw"]: 
        #session["user_name"] = result[0]["name"]

        # sessionの有効期限
        #session.permanent = True
        #app.permanent_session_lifetime = timedelta(minutes=30)
        return render_template("u_add_1.html.html")
    else:
        return redirect(url_for("u_login_page")) 


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
    dbmg.calc_pw_hash(pw)

    return render_template("u_signup_2.html",result=param)

if __name__ == "__main__":
    app.run(debug=True)