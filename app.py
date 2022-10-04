from flask import Flask, render_template, request
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

    dbmg = db_manager
    dbmg.exec_query("select * from u_account")

    return render_template("u_signup_2.html",result=param)

if __name__ == "__main__":
    app.run(debug=True)