from flask import Flask, render_template, request, redirect, url_for, session
import datetime
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
        app.permanent_session_lifetime = datetime.timedelta(minutes=30)
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
    #選考中の企業表示
    dbmg = db_manager()
    sql = "select * from schedule as s1 where id = %s and s1.date_time = (select max(s2.date_time) from schedule as s2 where s1.company = s2.company group by s2.company) order by date_time asc;"
    result = dbmg.exec_query(sql, session["id"])

    #print(result)

    return render_template("u_home.html",result=result)

@app.route("/u_modify")
def u_modify_page():
    company = request.args.get("company")
    return render_template("u_modify_1.html", company=company)

@app.route("/u_modify/confirm", methods=["POST"])
def u_modify_confirm():
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    schedule = {"step":step,"detail":detail,"place":place,"date_time":date_time}

    return render_template("u_modify_2.html", company=company, schedule=schedule)

@app.route("/u_modify/done", methods=["POST"])
def u_modify():
    id = session["id"]
    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    dbmg = db_manager()
    sql = "update schedule set step=%s, detail=%s, place=%s, date_time=%s where id=%s and company=%s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch);"
    dbmg.exec_query(sql,(step, detail, place, date_time, id, company, id, company))

    return render_template("u_modify_3.html")

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
    company = request.args.get("company")
    return render_template("u_register_1.html",company=company)

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

@app.route("/u_company")
def u_company_page():
    id = session["id"]
    company = request.args.get("company")

    dbmg = db_manager()
    sql = "select * from schedule where id=%s and company=%s order by date_time desc"
    schedule = dbmg.exec_query(sql,(id,company))

    return render_template("u_company.html",company=company, schedule=schedule)

@app.route("/u_delete")
def u_delete_page():
    company = request.args.get("company")
    return render_template("u_delete_1.html",company=company)

@app.route("/u_delete/u_delete2")
def u_delete():
    id = session["id"]
    company = request.args.get("company")
    dbmg = db_manager()
    dbmg.exec_query("delete from schedule where id=%s and company=%s",(id,company))
    return render_template("u_delete_2.html",company=company)

@app.route("/u_check")
def u_check_page():
    dbmg = db_manager()
    teachers = dbmg.exec_query("select * from a_account")
    return render_template("u_check_1.html",teachers=teachers)

@app.route("/u_check/confirm", methods=["POST"])
def u_check_confirm():
    teacher = request.form.get("teacher")
    title = request.form.get("title")
    body = request.form.get("body")

    check = {"teacher":teacher,"title":title,"body":body}

    return render_template("u_check_2.html", check=check)

@app.route("/u_check/done", methods=["POST"])
def u_check():
    student = session["id"]
    teacher = request.form.get("teacher")
    title = request.form.get("title")
    body = request.form.get("body")

    dbmg = db_manager()
    dbmg.exec_query("insert into review(student,teacher,title,body,check_flg,propriety_flg) values(%s,%s,%s,%s,%s,%s)",(student,teacher,title,body,0,0))

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
    return render_template("u_account_1.html")

@app.route("/u_account", methods=["POST"])
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

if __name__ == "__main__":
    app.run(debug=True)