from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import random, string
from pymysql import IntegrityError
from db.db_manager import db_manager
#from plyer import notification

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

# 定数

## セッションの有効期限（単位：分）
SESSION_LIFETIME_MINUTES = 30

# 関数

## 学科・学年・組を取得する関数
def get_classes():
    dbmg = db_manager()
    
    deps = dbmg.exec_query("select * from dep")

    this_year = datetime.date.today().year - 2000
    grad_years = [this_year + 1,this_year + 2, this_year + 3, this_year + 4]

    return deps,grad_years

@app.route("/")
def u_login_page():
    return render_template("u_login.html")

@app.route("/",methods=["POST"])
def u_login():
    id = request.form.get("id")
    pw = request.form.get("pw")
    
    dbmg = db_manager()
    user = dbmg.exec_query("select * from u_account where id=%s",id)

    # 入力された id が存在しない場合
    if len(user) == 0:
        return redirect("/")

    hash_pw,_ = dbmg.calc_pw_hash(pw,user[0]["salt"])

    if hash_pw == user[0]["hash_pw"]:
        session["id"] = user[0]["id"]
        # sessionの有効期限を設定
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=SESSION_LIFETIME_MINUTES)
        return redirect("/home")
    else:
        return redirect("/") 


@app.route("/u_signup")
def u_signup_page():
    deps,grad_years = get_classes()
    return render_template("u_signup_1.html",deps=deps,grad_years=grad_years)

@app.route("/u_signup",methods=["POST"])
def u_signup():
    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    dep = request.form.get("dep")
    graduation = request.form.get("graduation")

    # 未入力の項目がある場合
    if not (id and pw and name and dep and graduation):
        return redirect(url_for("u_signup_page"))

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    class_id = graduation + dep

    try:
        dbmg.exec_query("insert into u_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,class_id))
    except IntegrityError:
        return redirect(url_for("u_signup_page"))

    return render_template("u_signup_3.html")

@app.route("/home")
def u_home_page():
    if "id" not in session:
        return redirect("/")

    dbmg = db_manager()

    # 企業ごとの最新の選考予定を表示
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and finished_flg = 0 and passed_flg = 0 order by date_time asc;"
    schedules = dbmg.exec_query(sql,session["id"])

    # 内定済の企業
    sql = "select company from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and passed_flg = 1 order by date_time asc;"
    passed_companies = dbmg.exec_query(sql,session["id"])

    # 選考終了済の企業
    sql = "select company from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and finished_flg = 1 order by date_time asc;"
    finished_companies = dbmg.exec_query(sql,session["id"])

    # 掲示板
    sql = "select * from threads order by last_update desc limit 3"
    threads = dbmg.exec_query(sql)

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("u_home.html",schedules=schedules,passed_companies=passed_companies,finished_companies=finished_companies,threads=threads)

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
    dbmg.exec_query("insert into schedule(id,company,date_time,step,detail,place) values(%s,%s,%s,%s,%s,%s)",schedule)

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
    dbmg.exec_query("insert into schedule(id,company,date_time,step,detail,place) values(%s,%s,%s,%s,%s,%s)",schedule)
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
    dbmg.exec_query("update schedule set finished_flg = %s where id = %s and company = %s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch)",(1,id,company,id,company))

    return render_template("u_delete_2.html",company=company)

@app.route("/u_passed")
def u_passed_page():
    company = request.args.get("company")
    return render_template("u_passed_1.html",company=company)

@app.route("/u_passed/done")
def u_passed():
    id = session["id"]
    company = request.args.get("company")

    dbmg = db_manager()
    dbmg.exec_query("update schedule set passed_flg = %s where id = %s and company = %s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch)",(1,id,company,id,company))

    return render_template("u_passed_2.html",company=company)

@app.route("/u_practice",methods=["GET","POST"])
def u_practice_page():
    student = session["id"]

    dbmg = db_manager()
    schedules = dbmg.exec_query("select practice.id as id,name as teacher,date,comment from practice inner join a_account on teacher = a_account.id where practice.id in (select schedule_id from practice_attendance where student=%s) order by date asc",student)
    teachers = dbmg.exec_query("select id,name from a_account")

    teacher = request.form.get("teacher")
    date = request.form.get("date")

    if request.method == "GET":
        return render_template("u_practice_home.html",teachers=teachers,schedules=schedules,method="get")
    
    if teacher:
        if date:
            search_result = dbmg.exec_query("select * from practice where teacher = %s and date <= %s and id not in (select schedule_id from practice_attendance where student=%s) order by date asc",(teacher,date,student))
        else:
            search_result = dbmg.exec_query("select * from practice where teacher = %s and id not in (select schedule_id from practice_attendance where student=%s) order by date asc",(teacher,student))
    else:
        if date:
            search_result = dbmg.exec_query("select * from practice where date <= %s and id not in (select schedule_id from practice_attendance where student=%s) order by date asc",(date,student))
        else:
            search_result = dbmg.exec_query("select * from practice where id not in (select schedule_id from practice_attendance where student=%s) order by date asc",student)

    return render_template("u_practice_home.html",teachers=teachers,search_result=search_result,schedules=schedules)

@app.route("/u_practice/confirm",methods=["GET","POST"])
def u_practice_confirm():
    id = request.args.get("id")

    dbmg = db_manager()

    practice = dbmg.exec_query("select practice.id,name as teacher,date,comment from practice inner join a_account on teacher = a_account.id where practice.id=%s",id)

    return render_template("u_practice_1.html",practice=practice[0])

@app.route("/u_practice/done")
def u_practice():
    id = request.args.get("id")
    student = session["id"]

    dbmg = db_manager()
    dbmg.exec_query("insert into practice_attendance values(%s,%s)",(id,student))
    
    return render_template("u_practice_2.html")

@app.route("/u_practice/detail")
def u_practice_detail():
    practice_id = request.args.get("id")

    dbmg = db_manager()
    practice = dbmg.exec_query("select practice.id as id,name as teacher,date,comment from practice inner join a_account on teacher=a_account.id where practice.id=%s",practice_id)
    
    return render_template("u_practice_detail.html",practice=practice[0])

@app.route("/u_practice/cancel")
def u_practice_cancel():
    practice_id = request.args.get("id")

    dbmg = db_manager()
    dbmg.exec_query("delete from practice_attendance where schedule_id=%s",practice_id)

    return render_template("u_practice_canceled.html")

@app.route("/u_check_home")
def u_check_home():
    id = session["id"]
    dbmg = db_manager()
    check = dbmg.exec_query("select a.id as id,b.name as name,a.title as title,a.check_flg as check_flg,a.date as date from review a,a_account b where a.teacher=b.id and a.student=%s",id)
    return render_template("u_check_home.html",check=check)

@app.route("/u_check_eva")
def u_check_eva():
    id = request.args.get("id")
    dbmg = db_manager()
    check = dbmg.exec_query("select a.id as id,b.name as name,a.title as title,a.check_flg as check_flg,a.date as date,a.body as body,a.comment as comment from review a,a_account b where a.teacher=b.id and a.id=%s",id)
    return render_template("u_check_eva.html",check=check)

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
        "date":request.form.get("date"),
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
        request.form.get("body"),
        request.form.get("date")
    )

    dbmg = db_manager()
    dbmg.exec_query("insert into review(student,teacher,title,body,date) values(%s,%s,%s,%s,%s)",check)

    return render_template("u_check_3.html")

@app.route("/u_search")
def u_search_page():
    return render_template("u_search.html")

@app.route("/u_forum")
def u_forum_page():

    dbmg = db_manager()
    threads = dbmg.exec_query("select * from threads order by last_update desc")

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("u_forum.html",threads=threads)

@app.route("/forum_build")
def forum_build_page():
    user = request.args.get("user")
    return render_template("forum_build.html",user=user)

@app.route("/forum_build/done")
def forum_build():
    id = session["id"]
    date_time = datetime.datetime.now()
    title = request.args.get("title")
    body = request.args.get("body")
    user = request.args.get("user")

    dbmg = db_manager()
    name = dbmg.exec_query("select name from u_account where id = %s",id)
    if name:
        name = name[0]["name"]
    else:
        name = dbmg.exec_query("select name from a_account where id = %s",id)
        name = name[0]["name"]
    dbmg.exec_query("insert into threads(title,author_id,author,last_contributer_id,last_contributer,last_update) values(%s,%s,%s,%s,%s,%s)",(title,id,name,id,name,date_time))
    
    thread_id = dbmg.exec_query("select id from threads where author_id=%s order by last_update desc limit 1",id)
    thread_id = thread_id[0]["id"]

    dbmg.exec_query("insert into comments(thread_id,contributer_id,contributer,date_time,body) values(%s,%s,%s,%s,%s)",(thread_id,id,name,date_time,body))

    return redirect(url_for("forum_brows",thread_id=thread_id,user=user))

@app.route("/forum_brows")
def forum_brows():
    thread_id = request.args.get("thread_id")
    user = request.args.get("user")

    dbmg = db_manager()
    thread = dbmg.exec_query("select * from threads where id = %s",thread_id)
    # sql修正必要
    comments = dbmg.exec_query("select * from comments where thread_id = %s",thread_id)

    return render_template("forum_brows.html",thread=thread[0],comments=comments,user=user)

@app.route("/forum_contribute")
def forum_contribute():
    id = session["id"]
    thread_id = request.args.get("thread_id")
    user = request.args.get("user")
    body = request.args.get("body")
    date_time = datetime.datetime.now()

    # commentsテーブルのcontributerをcontributer_idに変更、contributer_nameを追加する必要がある
    dbmg = db_manager()
    name = dbmg.exec_query("select name from u_account where id = %s",id)
    if name:
        name = name[0]["name"]
    else:
        name = dbmg.exec_query("select name from a_account where id = %s",id)
        name = name[0]["name"]
    dbmg.exec_query("insert into comments(thread_id,contributer_id,contributer,date_time,body) values(%s,%s,%s,%s,%s)",(thread_id,id,name,date_time,body))
    dbmg.exec_query("update threads set last_contributer_id = %s,last_contributer = %s where id = %s",(id,name,thread_id))

    return redirect(url_for("forum_brows",thread_id=thread_id,user=user))

@app.route("/u_account")
def u_account_page():
    deps,grad_years = get_classes()
    return render_template("u_account_1.html",deps=deps,grad_years=grad_years)

@app.route("/u_account",methods=["POST"])
def u_account():
    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year = request.form.get("grad_year")
    dep = request.form.get("dep")

    class_id = grad_year + dep

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

@app.route("/a_login")
def a_login_page():
    return render_template("a_login.html")

@app.route("/a_login",methods=["POST"])
def a_login():
    id = request.form.get("id")
    pw = request.form.get("pw")
    
    dbmg = db_manager()
    user = dbmg.exec_query("select * from a_account where id=%s",id)

    # 入力された id が存在しない場合
    if len(user) == 0:
        return redirect("/a_login")

    hash_pw,_ = dbmg.calc_pw_hash(pw,user[0]["salt"])

    if hash_pw == user[0]["hash_pw"]:
        session["id"] = user[0]["id"]
        # sessionの有効期限
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=SESSION_LIFETIME_MINUTES)
        return redirect("/a_home")
    else:
        return redirect("/a_login") 

@app.route("/a_home")
def a_home_page():
    if "id" not in session:
        return redirect("/")
    id = session["id"]
    dbmg = db_manager()
    date = str(datetime.date.today())
    date_time_s = date + " " + "00:00:00"
    date_time_e = date + " " + "23:59:59"
    
    """
        notification.notify(
        title="予定",
        message="選考予定の生徒がいます",
        app_name="JBRecluit",
        app_icon="static/img/favicon.ico",
        timeout=10
    )
    """
    

    #本日選考予定(sql変更予定)
    sql = "select u_account.name as name,schedule.company as company,schedule.step as step,schedule.detail as detail,substring(schedule.date_time,12,5) as date_time from schedule left join u_account on schedule.id = u_account.id where date_time <= %s and date_time >= %s"
    schedules = dbmg.exec_query(sql,(date_time_e,date_time_s))
    sql = "select d.name as dep,b.name as name,right(date,5) as date from practice a,u_account b,class c,dep d where a.student = b.id and b.class_id = c.id and c.dep_id = d.id and a.teacher = %s"
    # practices = dbmg.exec_query(sql,(id))
    practices = []
    #文章チェック
    sql = "select student,title from review where teacher = %s and check_flg = 0"
    reviews = dbmg.exec_query(sql,(id))
    return render_template("a_home.html",schedules=schedules,practices=practices,reviews=reviews)

@app.route("/a_signup")
def a_signup_page():
    deps,grad_years = get_classes()
    return render_template("a_signup_1.html",deps=deps,grad_years=grad_years)

@app.route("/a_signup",methods=["POST"])
def a_signup():
    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    class_id1 = grad_year1 + dep1
    class_id2 = grad_year2 + dep2

    dbmg.exec_query("insert into a_account(id,hash_pw,salt,name) values(%s,%s,%s,%s)",(id,hash_pw,salt,name))
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id2))

    return render_template("a_signup_3.html")

@app.route("/a_all")
def a_all_page():
    id = session["id"]
    class_id = request.args.get('class_id')

    dbmg = db_manager()
    classes = dbmg.exec_query("select class_id,cast(graduation as char) as grad_year,name as dep from teacher_class inner join class on class_id = class.id inner join dep on dep_id = dep.id where teacher_class.id=%s",id)
    if class_id:
        schedules = dbmg.exec_query("select schedule.id as id,name,cast(count(company) as char) as num from schedule inner join u_account on schedule.id = u_account.id where class_id = %s group by schedule.id",class_id)
        print(schedules)
        return render_template("a_all.html",classes=classes,schedules=schedules)
    else:
        return render_template("a_all.html",classes=classes)

@app.route("/a_student")
def a_student_page():
    id = request.args.get("id")

    dbmg = db_manager()
    student = dbmg.exec_query("select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where u_account.id=%s",id)
    schedules = dbmg.exec_query("select * from schedule as s1 where id = %s and s1.date_time = (select max(s2.date_time) from schedule as s2 where s1.company = s2.company group by s2.company) order by date_time asc",id)

    return render_template("a_student.html",student=student[0],schedules=schedules)

@app.route("/a_forum")
def a_forum_page():
    dbmg = db_manager()
    threads = dbmg.exec_query("select * from threads order by last_update desc")

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("a_forum.html",threads=threads)

@app.route("/a_practice")
def a_practice_page():
    teacher = session["id"]

    dbmg = db_manager()
    schedules = dbmg.exec_query("select * from practice where teacher = %s order by date asc",(teacher))

    return render_template("a_practice_home.html",schedules=schedules)

@app.route("/a_practice_1")
def a_practice_1():
    return render_template("a_practice_1.html")

@app.route("/a_practice_2")
def a_practice_2():
    date = request.args.get("date")
    comment = request.args.get("comment")

    return render_template("a_practice_2.html",date=date,comment=comment)

@app.route("/a_practice_3",methods=["POST"])
def a_practice_3():
    teacher = session["id"]
    date = request.form.get("date")
    comment = request.form.get("comment")

    dbmg = db_manager()
    dbmg.exec_query("insert into practice(teacher,date,comment) values(%s,%s,%s)",(teacher,date,comment))

    return render_template("a_practice_3.html")

@app.route("/a_practice/detail",methods=["GET","POST"])
def a_practice_detail():
    id = request.args.get("id")

    dbmg = db_manager()

    if request.method == "POST":
        comment = request.form.get("comment")
        dbmg.exec_query("update practice set comment=%s where id=%s",(comment,id))

    practice = dbmg.exec_query("select * from practice where id=%s",id)

    return render_template("a_practice_detail.html",practice=practice[0])

@app.route("/a_check_all")
def a_check_page():
    id = session["id"]
    dbmg = db_manager()
    sql = "select a.id as id,b.name as name,a.title as title,a.check_flg as check_flg,a.date as date from review a,u_account b where a.student=b.id and a.teacher=%s"
    result = dbmg.exec_query(sql,(id))
    return render_template("a_check_all.html",result=result)

@app.route("/a_check")
def a_check():
    id = request.args.get("id")
    print(id)
    dbmg = db_manager()
    sql = "select a.id as id,b.name as name,a.title as title,a.check_flg as check_flg,a.date as date,a.body as body,a.comment as comment from review a,u_account b where a.student=b.id and a.id=%s"
    result = dbmg.exec_query(sql,(id))
    print(result)
    if result[0]["check_flg"]==0:
        sql = "update review set check_flg=1 where id=%s"
        dbmg.exec_query(sql,(id))
    print(result[0])
    return render_template("a_check.html",result=result)

@app.route("/a_check_comment",methods=["POST"])
def a_check_comment():
    comment = request.form.get("comment")
    id = request.form.get("id")
    dbmg = db_manager()
    sql = "update review set comment=%s where id=%s"
    dbmg.exec_query(sql,(comment,id))
    sql = "select a.id as id,b.name as name,a.title as title,a.check_flg as check_flg,a.date as date,a.body as body,a.comment as comment from review a,u_account b where a.student=b.id and a.id=%s"
    result = dbmg.exec_query(sql,(id))
    return render_template("a_check.html",result=result)

@app.route("/a_check_flg")
def a_check_flg():
    id = request.args.get("id")
    flg = request.args.get("flg")
    dbmg = db_manager()
    sql = "update review set check_flg = %s where id = %s"
    dbmg.exec_query(sql,(flg,id))
    sql = "select a.id as id,d.name as dep,c.grade as grade,c.class as class,b.name as name,a.title as title,a.body as body from review a,u_account b,class c,dep d where a.student = b.id and b.class_id = c.id and c.dep_id = d.id and a.id = %s"
    result = dbmg.exec_query(sql,(id))
    # return render_template("a_check.html",result=result[0])
    return redirect("/a_check_all")

@app.route("/a_thread")
def a_thread_page():
    id = request.args.get("id")
    return render_template("a_thread_1.html",id=id)

@app.route("/a_thread/done")
def a_thread_delete():
    id = request.args.get("id")

    dbmg = db_manager()
    dbmg.exec_query("delete from threads where id = %s",id)
    dbmg.exec_query("delete from comments where thread_id = %s",id)

    return render_template("a_thread_2.html")

@app.route("/a_account")
def a_account_page():
    id = session["id"]
    deps,grad_years = get_classes()
    return render_template("a_account_1.html",id=id,deps=deps,grad_years=grad_years)

@app.route("/a_account",methods=["POST"])
def a_account():
    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")

    class_id1 = grad_year1 + dep1
    class_id2 = grad_year2 + dep2

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    sql = "update a_account set hash_pw=%s, salt=%s, name=%s where id=%s"
    dbmg.exec_query(sql, (hash_pw, salt, name, id))

    dbmg.exec_query("delete from teacher_class where id = %s",id)
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id2))

    return render_template("a_account_3.html")

@app.route("/a_user_account/search",methods=["GET","POST"])
def a_user_account_page():
    dbmg = db_manager()

    deps,grad_years = get_classes()
    
    id = request.form.get("id")
    grad_year = request.form.get("grad_year")
    dep = request.form.get("dep")
    name = request.form.get("name")

    # DBで検索するために変形
    if grad_year != None:
        grad_year = grad_year + "%"
    if dep != None:
        dep = "%" + dep
    if name != None:
        name = "%" + name + "%"

    if request.method == "GET":
        return render_template("a_user_account_1.html",deps=deps,grad_years=grad_years)

    if id:
        users = dbmg.exec_query("select u_account.id as id,u_account.name as name,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where u_account.id = %s",id)
    else:
        users = dbmg.exec_query("select u_account.id as id,u_account.name as name,graduation as grad_year,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where class_id like %s and class_id like %s and dep.name like %s",(grad_year,dep,name))

    return render_template("a_user_account_1.html",deps=deps,users=users)

@app.route("/a_user_account/confirm",methods=["POST"])
def a_user_account_confirm():
    user = {
        "id":request.form.get("id"),
        "name":request.form.get("name"),
        "grad_year":request.form.get("grad_year"),
        "dep":request.form.get("dep")
    }
    return render_template("a_user_account_2.html",user=user)

@app.route("/a_user_account/done")
def a_user_account_done():
    id = request.args.get("id")

    dbmg = db_manager()
    dbmg.exec_query("delete from u_account where id = %s",id)

    return render_template("a_user_account_3.html")

if __name__ == "__main__":
    app.run(debug=True)