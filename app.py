from flask import Flask, render_template, request, redirect, url_for, session
import datetime
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
    
    dbmg = db_manager()
    user = dbmg.exec_query("select * from u_account where id=%s",id)

    hash_pw,_ = dbmg.calc_pw_hash(pw,user[0]["salt"])

    if hash_pw == user[0]["hash_pw"]:
        session["id"] = user[0]["id"]
        # sessionの有効期限
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=30)
        return redirect("/home")
    else:
        return redirect("/") 


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

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    class_id = dep + grade + Class

    dbmg.exec_query("insert into u_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,class_id))

    return render_template("u_signup_3.html")

@app.route("/home")
def u_home_page():
    if "id" not in session:
        return redirect("/")

    # 選考中の企業表示
    dbmg = db_manager()
    sql = "select * from schedule as s1 where id = %s and s1.date_time = (select max(s2.date_time) from schedule as s2 where s1.company = s2.company group by s2.company) order by date_time asc;"
    schedules = dbmg.exec_query(sql,session["id"])

    return render_template("u_home.html",schedules=schedules)

@app.route("/u_company")
def u_company_page():
    id = session["id"]
    company = request.args.get("company")

    dbmg = db_manager()
    sql = "select * from schedule where id=%s and company=%s order by date_time desc"
    schedules = dbmg.exec_query(sql,(id,company))

    return render_template("u_company.html", schedules=schedules)

@app.route("/u_add")
def u_add_page():
    return render_template("u_add_1.html")

@app.route("/u_add/confirm",methods=["POST"])
def u_add_confirm():
    schedule = {
        "company":request.form.get("company"),
        "step":request.form.get("step"),
        "detail":request.form.get("detail"),
        "place":request.form.get("place"),
        "date_time":request.form.get("date_time")
    }
    return render_template("u_add_2.html",schedule=schedule)

@app.route("/u_add/done",methods=["POST"])
def u_add():
    schedule = (
        session["id"],
        request.form.get("company"),
        request.form.get("date_time"),
        request.form.get("step"),
        request.form.get("detail"),
        request.form.get("place")
    )

    dbmg = db_manager()
    dbmg.exec_query("insert into schedule values(%s,%s,%s,%s,%s,%s)",schedule)

    return render_template("u_add_3.html")

@app.route("/u_register")
def u_register_page():
    company = request.args.get("company")
    return render_template("u_register_1.html",company=company)

@app.route("/u_register/confirm",methods=["POST"])
def u_register_confirm():
    schedule = {
        "company":request.form.get("company"),
        "step":request.form.get("step"),
        "detail":request.form.get("detail"),
        "place":request.form.get("place"),
        "date_time":request.form.get("date_time")
    }
    return render_template("u_register_2.html",schedule=schedule)

@app.route("/u_register/done",methods=["POST"])
def u_register():
    company = request.form.get("company")
    schedule = (
        session["id"],
        request.form.get("company"),
        request.form.get("date_time"),
        request.form.get("step"),
        request.form.get("detail"),
        request.form.get("place")
    )

    dbmg = db_manager()
    dbmg.exec_query("insert into schedule values(%s,%s,%s,%s,%s,%s)",schedule)
    return render_template("u_register_3.html",company=company)

@app.route("/u_modify")
def u_modify_page():
    company = request.args.get("company")
    return render_template("u_modify_1.html",company=company)

@app.route("/u_modify/confirm",methods=["POST"])
def u_modify_confirm():
    schedule = {
        "company":request.form.get("company"),
        "step":request.form.get("step"),
        "detail":request.form.get("detail"),
        "place":request.form.get("place"),
        "date_time":request.form.get("date_time")
    }

    return render_template("u_modify_2.html",schedule=schedule)

@app.route("/u_modify/done",methods=["POST"])
def u_modify():
    company = request.form.get("company")
    schedule = (
        request.form.get("step"),
        request.form.get("detail"),
        request.form.get("place"),
        request.form.get("date_time"),
        session["id"],
        request.form.get("company"),
        session["id"],
        request.form.get("company")
    )

    dbmg = db_manager()
    sql = "update schedule set step=%s, detail=%s, place=%s, date_time=%s where id=%s and company=%s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch);"
    dbmg.exec_query(sql,schedule)

    return render_template("u_modify_3.html",company=company)

@app.route("/u_delete")
def u_delete_page():
    company = request.args.get("company")
    return render_template("u_delete_1.html",company=company)

@app.route("/u_delete/done")
def u_delete():
    id = session["id"]
    company = request.args.get("company")

    dbmg = db_manager()
    dbmg.exec_query("delete from schedule where id=%s and company=%s",(id,company))

    return render_template("u_delete_2.html",company=company)

@app.route("/u_men")
def u_men_page():
    dbmg = db_manager()
    teachers = dbmg.exec_query("select id,name from a_account")

    return render_template("u_men_1.html",teachers=teachers)

@app.route("/u_men/confirm",methods=["POST"])
def u_men_confirm():
    id = request.form.get("id")

    dbmg = db_manager()
    teacher = dbmg.exec_query("select name from a_account where id=%s",id)

    practice = {
        "id":id,
        "name":teacher[0]["name"],
        "date":request.form.get("date"),
        "time":request.form.get("time")
    }

    return render_template("u_men_2.html",practice=practice)

@app.route("/u_men/done",methods=["POST"])
def u_men():
    practice = (
        session["id"],
        request.form.get("id"),
        request.form.get("date"),
        request.form.get("time")
    )
    
    dbmg = db_manager()
    dbmg.exec_query("insert into practice(student,teacher,date,time) values(%s,%s,%s,%s)",practice)
    
    return render_template("u_men_3.html")

@app.route("/u_check")
def u_check_page():
    dbmg = db_manager()
    teachers = dbmg.exec_query("select * from a_account")

    return render_template("u_check_1.html",teachers=teachers)

@app.route("/u_check/confirm",methods=["POST"])
def u_check_confirm():
    id = request.form.get("id")

    dbmg = db_manager()
    teacher = dbmg.exec_query("select name from a_account where id=%s",id)

    check = {
        "id":id,
        "name":teacher[0]["name"],
        "title":request.form.get("title"),
        "body":request.form.get("body")
    }

    return render_template("u_check_2.html", check=check)

@app.route("/u_check/done",methods=["POST"])
def u_check():
    check = (
        session["id"],
        request.form.get("id"),
        request.form.get("title"),
        request.form.get("body")
    )

    dbmg = db_manager()
    dbmg.exec_query("insert into review(student,teacher,title,body) values(%s,%s,%s,%s)",check)

    return render_template("u_check_3.html")

@app.route("/u_search")
def u_search_page():
    return render_template("u_search.html")

@app.route("/u_forum")
def u_forum_page():

    dbmg = db_manager()
    threads = dbmg.exec_query("select * from threads")

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("u_forum.html",threads=threads)

@app.route("/forum_build")
def forum_build_page():
    return render_template("forum_build.html")

@app.route("/forum_build/done")
def forum_build():
    id = session["id"]
    date_time = datetime.datetime.now()
    title = request.args.get("title")
    body = request.args.get("body")

    dbmg = db_manager()
    dbmg.exec_query("insert into threads(title,author,last_contributer,last_update) values(%s,%s,%s,%s)",(title,id,id,date_time))
    
    thread_id = dbmg.exec_query("select id from threads where author=%s order by last_update desc limit 1",id)
    thread_id = thread_id[0]["id"]

    dbmg.exec_query("insert into comments(thread_id,contributer,date_time,body) values(%s,%s,%s,%s)",(thread_id,id,date_time,body))

    return redirect(url_for("forum_brows",thread_id=thread_id))

@app.route("/forum_brows")
def forum_brows():
    thread_id = request.args.get("thread_id")

    dbmg = db_manager()
    thread = dbmg.exec_query("select * from threads where id = %s",thread_id)
    comments = dbmg.exec_query("select * from comments where thread_id = %s",thread_id)

    return render_template("forum_brows.html",thread=thread[0],comments=comments)

@app.route("/forum_contribute")
def forum_contribute():
    id = session["id"]
    thread_id = request.args.get("thread_id")
    body = request.args.get("body")
    date_time = datetime.datetime.now()

    dbmg = db_manager()
    dbmg.exec_query("insert into comments(thread_id,contributer,date_time,body) values(%s,%s,%s,%s)",(thread_id,id,date_time,body))

    return redirect(url_for("forum_brows",thread_id=thread_id))

@app.route("/u_account")
def u_account_page():
    dbmg = db_manager()

    # プルダウンに表示する学科・学年・組を取得し、配列に格納する
    dep_ids_dict = dbmg.exec_query("select distinct dep_id from class")
    grades_dict = dbmg.exec_query("select distinct grade from class")
    classes_dict = dbmg.exec_query("select distinct class from class")

    deps = []
    for dep_ids in dep_ids_dict:
        dep = dbmg.exec_query("select * from dep where id=%s",dep_ids["dep_id"])
        deps.append(dep[0])

    grades = []
    for grade in grades_dict:
        grades.append(grade)

    classes = []
    for Class in classes_dict:
        classes.append(Class)

    return render_template("u_account_1.html",deps=deps,grades=grades,classes=classes)

@app.route("/u_account",methods=["POST"])
def u_account():
    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    dep = request.form.get("dep")
    grade = request.form.get("grade")
    Class = request.form.get("class") # 区別のためcは大文字

    class_id = dep + grade + Class

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    sql = "update u_account set hash_pw=%s, salt=%s, name=%s, class_id=%s where id=%s"
    dbmg.exec_query(sql, (hash_pw, salt, name, class_id, id))

    return render_template("u_account_3.html")

@app.route("/logout")
def logout():
    if "id" in session:
        session.pop("id",None)   # セッションを空にする
    
    return redirect("/")

#ここから管理者------------------------------------------------------------------------------------
@app.route("/a_login")
def a_login_page():
    return render_template("a_login.html")

@app.route("/a_login",methods=["POST"])
def a_login():
    id = request.form.get("id")
    pw = request.form.get("pw")
    
    dbmg = db_manager()
    user = dbmg.exec_query("select * from a_account where id=%s",id)

    hash_pw,_ = dbmg.calc_pw_hash(pw,user[0]["salt"])

    if hash_pw == user[0]["hash_pw"]:
        session["id"] = user[0]["id"]
        # sessionの有効期限
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=30)
        return redirect("/a_home")
    else:
        return redirect("/a_login") 

@app.route("/a_home")
def a_home_page():
    if "id" not in session:
        return redirect("/")
    dbmg = db_manager()
    date = str(datetime.date.today())
    date_time_s = date + " " + "00:00:00"
    date_time_e = date + " " + "23:59:59"
    sql = "select u_account.name as name,schedule.company as company,schedule.step as step,schedule.detail as detail,substring(schedule.date_time,12,5) as date_time from schedule left join u_account on schedule.id = u_account.id where date_time <= %s and date_time >= %s"
    schedules = dbmg.exec_query(sql,(date_time_e,date_time_s))
    return render_template("a_home.html",schedules=schedules)

if __name__ == "__main__":
    app.run(debug=True)