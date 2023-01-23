from flask import Flask,render_template,request,redirect,url_for,session
import datetime
import random,string
import glob
from db.db_manager import db_manager
from pymysql import IntegrityError

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

# 定数 --------------------------------------------------------------------------

SESSION_LIFETIME_MINUTES = 30

# 関数 --------------------------------------------------------------------------

def get_classes():
    dbmg = db_manager()

    this_year = datetime.date.today().year - 2000
    grad_years = [this_year,this_year + 1,this_year + 2, this_year + 3, this_year + 4]
    
    deps = dbmg.exec_query("select * from dep")

    return grad_years,deps

# 利用者の処理 ---------------------------------------------------------

@app.route("/")
def u_login_page():
    if "id" not in session:
        return render_template("u_login.html")
    if session["user"] == "user" :
        return redirect("/u_home")
    if session["user"] == "admin":
        return redirect("/a_home")

@app.route("/",methods=["POST"])
def u_login():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    
    # 入力されたIDが存在しない場合
    account = dbmg.exec_query("select * from u_account where id=%s",id)
    if len(account) == 0:
        return redirect("/")

    hash_pw,_ = dbmg.calc_pw_hash(pw,account[0]["salt"])

    if hash_pw == account[0]["hash_pw"]:
        session["id"] = account[0]["id"]
        session["user"] = "user"
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(hours=168) # 定数？
        return redirect("/u_home")
    else:
        # パスワードが間違っている場合
        return redirect("/")

@app.route("/u_signup")
def u_signup_page():
    e = request.args.get("e")
    grad_years,deps = get_classes()
    return render_template("u_signup_1.html",grad_years=grad_years,deps=deps,e=e)

@app.route("/u_signup/confirm",methods=["POST"])
def u_signup_confirm():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year = request.form.get("grad_year")
    dep_id = request.form.get("dep")

    # 未入力の項目がある場合
    if not (id and pw and name and grad_year and dep_id):
        return redirect(url_for("u_signup_page"))
    
    # idが既に使われている場合
    id_check = dbmg.exec_query("select * from u_account where id=%s",id)
    if len(id_check) != 0:
        return redirect(url_for("u_signup_page",e=1))
    
    # idが7文字でない場合（HTML側でも制御している）
    if len(id) != 7:
        return redirect(url_for("u_signup_page"))

    # idが文字列の場合
    try:
        int(id)
    except ValueError:
        return redirect(url_for("u_signup_page"))

    # idが不正な場合
    if int(id) < 1000000:
        return redirect(url_for("u_signup_page"))

    # pwの文字数が不正な場合（HTML側でも制御している）
    if len(pw) < 8 or len(pw) > 20:
        return redirect(url_for("u_signup_page"))

    # nameの文字数が不正な場合（HTML側でも制御している）
    if len(name) > 16:
        return redirect(url_for("u_signup_page"))
    
    dep = dbmg.exec_query("select * from dep where id=%s",dep_id)[0]

    account = {
        "id":id,
        "pw":pw,
        "name":name,
        "grad_year":grad_year,
        "dep":dep
    }

    return render_template("u_signup_2.html",account=account)

@app.route("/u_signup/done",methods=["POST"])
def u_signup():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year = request.form.get("grad_year")
    dep_id = request.form.get("dep")

    hash_pw,salt = dbmg.calc_pw_hash(pw)
    class_id = grad_year + dep_id

    dbmg.exec_query("insert into u_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,class_id))

    return render_template("u_signup_3.html")

@app.route("/u_home")
def u_home_page():
    if "id" not in session:
        return redirect("/")

    dbmg = db_manager()

    id = session["id"]

    # 企業ごとの最新の選考予定を表示
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and finished_flg = 0 and passed_flg = 0 order by date_time asc;"
    schedules = dbmg.exec_query(sql,(id,id))

    for sc in schedules :
        dt = sc["date_time"]
        today = datetime.datetime.now()
        if dt < today :
            sc["red"] = True  
        else :
            sc["red"] = False

    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]

    # 内定済の企業
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and passed_flg = 1 order by date_time asc;"
    passed_companies = dbmg.exec_query(sql,(id,id))

    # 選考終了済の企業
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and finished_flg = 1 order by date_time asc;"
    finished_companies = dbmg.exec_query(sql,(id,id))

    # 掲示板
    sql = "select * from threads order by last_update desc limit 3"
    threads = dbmg.exec_query(sql)

    for thread in threads:
        # コメント数の要素を追加
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("u_home.html",schedules=schedules,passed_companies=passed_companies,finished_companies=finished_companies,threads=threads)

@app.route("/u_company")
def u_company_page():
    dbmg = db_manager()

    id = session["id"]
    company = request.args.get("company")

    sql = "select * from schedule where id = %s and company = %s order by date_time desc"
    schedules = dbmg.exec_query(sql,(id,company))

    for sc in schedules :
        dt = sc["date_time"]
        today = datetime.datetime.now()
        if dt < today :
            sc["red"] = True  
        else :
            sc["red"] = False

    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]

    return render_template("u_company.html", schedules=schedules)

@app.route("/u_company/readonly")
def u_company_readonly():
    dbmg = db_manager()

    id = request.args.get("id")
    company = request.args.get("company")
    state = request.args.get("state")

    sql = "select * from schedule where id = %s and company = %s order by date_time desc"
    schedules = dbmg.exec_query(sql,(id,company))

    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]

    return render_template("u_company_readonly.html",schedules=schedules,state=state)

@app.route("/u_add")
def u_add_page():
    return render_template("u_add_1.html")

@app.route("/u_add/confirm",methods=["POST"])
def u_add_confirm():
    dbmg = db_manager()

    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    # 未入力
    if not (company and step and detail and place and date_time):
        return redirect(url_for("u_add_page"))

    # companyの文字数
    if len(company) > 64:
        return redirect(url_for("u_add_page"))

    # 日付が過去の場合
    date_check = datetime.datetime.strptime(date_time + ":00", '%Y-%m-%dT%H:%M:%S')
    today = datetime.datetime.now()
    if date_check < today:
        return redirect(url_for("u_add_page"))
    
    # 既に登録されている企業の場合
    id = session["id"]
    schedule_check = dbmg.exec_query("select * from schedule where id=%s and company=%s",(id,company))
    if schedule_check:
        return redirect(url_for("u_add_page"))

    schedule = {
        "company":company,
        "step":step,
        "detail":detail,
        "place":place,
        "date_time":{
            "value":date_time,
            "display":date_time.replace("T"," ")
        }
    }
    
    return render_template("u_add_2.html",schedule=schedule)

@app.route("/u_add/done",methods=["POST"])
def u_add():
    dbmg = db_manager()

    schedule = (
        session["id"],
        request.form.get("company"),
        request.form.get("date_time"),
        request.form.get("step"),
        request.form.get("detail"),
        request.form.get("place")
    )

    sql = "insert into schedule(id,company,date_time,step,detail,place) values(%s,%s,%s,%s,%s,%s)"
    dbmg.exec_query(sql,schedule)

    return render_template("u_add_3.html")

@app.route("/u_register")
def u_register_page():
    company = request.args.get("company")
    return render_template("u_register_1.html",company=company)

@app.route("/u_register/confirm",methods=["POST"])
def u_register_confirm():
    dbmg = db_manager()

    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    # 未入力
    if not (company and step and detail and place and date_time):
        return redirect(url_for("u_register_page",company=company))

    # 日付が過去の場合
    date_check = datetime.datetime.strptime(date_time + ":00", '%Y-%m-%dT%H:%M:%S')
    today = datetime.datetime.now()
    if date_check < today:
        return redirect(url_for("u_register_page",company=company))
    
    # 既に登録されている予定の場合
    id = session["id"]
    schedule_check = dbmg.exec_query("select * from schedule where id=%s and company=%s and date_time=%s",(id,company,date_time))
    if schedule_check:
        return redirect(url_for("u_register_page",company=company))

    schedule = {
        "company":company,
        "step":step,
        "detail":detail,
        "place":place,
        "date_time":{
            "value":date_time,
            "display":date_time.replace("T"," ")
        }
    }

    return render_template("u_register_2.html",schedule=schedule)

@app.route("/u_register/done",methods=["POST"])
def u_register():
    dbmg = db_manager()

    company = request.form.get("company")

    schedule = (
        session["id"],
        request.form.get("company"),
        request.form.get("date_time"),
        request.form.get("step"),
        request.form.get("detail"),
        request.form.get("place")
    )

    sql = "insert into schedule(id,company,date_time,step,detail,place) values(%s,%s,%s,%s,%s,%s)"
    dbmg.exec_query(sql,schedule)
    return render_template("u_register_3.html",company=company)

@app.route("/u_modify")
def u_modify_page():
    company = request.args.get("company")
    return render_template("u_modify_1.html",company=company)

@app.route("/u_modify/confirm",methods=["POST"])
def u_modify_confirm():
    dbmg = db_manager()

    company = request.form.get("company")
    step = request.form.get("step")
    detail = request.form.get("detail")
    place = request.form.get("place")
    date_time = request.form.get("date_time")

    # 未入力
    if not (company and step and detail and place and date_time):
        return redirect(url_for("u_register_page",company=company))

    # 日付が過去の場合
    date_check = datetime.datetime.strptime(date_time + ":00", '%Y-%m-%dT%H:%M:%S')
    today = datetime.datetime.now()
    if date_check < today:
        return redirect(url_for("u_register_page",company=company))
    
    # 既に登録されている予定の場合
    id = session["id"]
    schedule_check = dbmg.exec_query("select * from schedule where id=%s and company=%s and date_time=%s",(id,company,date_time))
    if schedule_check:
        return redirect(url_for("u_register_page",company=company))

    schedule = {
        "company":company,
        "step":step,
        "detail":detail,
        "place":place,
        "date_time":{
            "value":date_time,
            "display":date_time.replace("T"," ")
        }
    }

    return render_template("u_modify_2.html",schedule=schedule)

@app.route("/u_modify/done",methods=["POST"])
def u_modify():
    dbmg = db_manager()

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

    sql = "update schedule set step=%s, detail=%s, place=%s, date_time=%s where id=%s and company=%s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch);"
    dbmg.exec_query(sql,schedule)

    return render_template("u_modify_3.html",company=company)

@app.route("/u_delete")
def u_delete_page():
    company = request.args.get("company")
    return render_template("u_delete_1.html",company=company)

@app.route("/u_delete/done")
def u_delete():
    dbmg = db_manager()

    id = session["id"]
    company = request.args.get("company")
    
    sql = "update schedule set finished_flg = %s where id = %s and company = %s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch)"
    dbmg.exec_query(sql,(True,id,company,id,company))

    return render_template("u_delete_2.html",company=company)

@app.route("/u_passed")
def u_passed_page():
    company = request.args.get("company")
    return render_template("u_passed_1.html",company=company)

@app.route("/u_passed/done")
def u_passed():
    dbmg = db_manager()

    id = session["id"]
    company = request.args.get("company")
    
    sql = "update schedule set passed_flg = %s where id = %s and company = %s and date_time = (select max(date_time) from (select date_time from schedule where id=%s and company=%s) as sch)"
    dbmg.exec_query(sql,(True,id,company,id,company))

    return render_template("u_passed_2.html",company=company)

@app.route("/u_practice",methods=["GET","POST"])
def u_practice_home():
    dbmg = db_manager()

    # 利用者が面接練習の中止を確認した場合
    if request.args.get("user_display_flg"):
        id = request.args.get("id")
        dbmg.exec_query("update practice set user_display_flg=%s where id=%s",(False,id))
        dbmg.exec_query("delete from practice_attendance where schedule_id=%s",id)

    student = session["id"]
    today = datetime.date.today()
    practices = dbmg.exec_query("select practice.id as id,name as teacher,date,comment,carrying_out_flg from practice inner join a_account on teacher = a_account.id where user_display_flg=%s and date>=%s and practice.id in (select schedule_id from practice_attendance where student=%s) order by date asc",(True,today,student))
    
    teachers = dbmg.exec_query("select id,name from a_account where public_flg=1")

    if request.method == "GET":
        return render_template("u_practice_home.html",teachers=teachers,practices=practices,method="get")

    teacher = request.form.get("teacher")
    teacher = "%" + teacher + "%"

    date = request.form.get("date")
    date = date if date else "2099-12-31"

    today = datetime.date.today()

    search_results = dbmg.exec_query("select practice.id as id,name as teacher,date,comment from practice inner join a_account on teacher=a_account.id where carrying_out_flg=%s and teacher like %s and date >= %s and date <= %s and practice.id not in (select schedule_id from practice_attendance where student=%s) order by date asc",(True,teacher,today,date,student))
    
    return render_template("u_practice_home.html",teachers=teachers,practices=practices,search_results=search_results)

@app.route("/u_practice/confirm",methods=["GET","POST"])
def u_practice_confirm():
    dbmg = db_manager()

    id = request.args.get("id")
    practice = dbmg.exec_query("select practice.id,name as teacher,date,comment from practice inner join a_account on teacher = a_account.id where practice.id=%s",id)

    return render_template("u_practice_1.html",practice=practice[0])

@app.route("/u_practice/done")
def u_practice():
    dbmg = db_manager()

    id = request.args.get("id")
    student = session["id"]

    dbmg.exec_query("insert into practice_attendance values(%s,%s)",(id,student))
    
    return render_template("u_practice_2.html")

@app.route("/u_practice/detail")
def u_practice_detail():
    dbmg = db_manager()

    id = request.args.get("id")
    practice = dbmg.exec_query("select practice.id as id,name as teacher,date,comment,carrying_out_flg from practice inner join a_account on teacher=a_account.id where practice.id=%s",id)
    
    return render_template("u_practice_detail.html",practice=practice[0])

@app.route("/u_practice/canceled")
def u_practice_canceled():
    dbmg = db_manager()

    student = session["id"]
    id = request.args.get("id")
    dbmg.exec_query("delete from practice_attendance where schedule_id=%s and student=%s",(id,student))

    return render_template("u_practice_canceled.html")

@app.route("/u_check")
def u_check_home():
    dbmg = db_manager()

    # u_check_detail で既読ボタンが押された場合
    check_id = request.args.get("check_id")
    if check_id:
        dbmg.exec_query("update review set read_flg=1 where id=%s",check_id)

    student_id = session["id"]
    read = dbmg.exec_query("select review.id as id,a_account.name as teacher,title,body,date,check_flg,read_flg,comment from review inner join a_account on teacher=a_account.id where read_flg=1 and student=%s order by date asc",student_id)
    unread = dbmg.exec_query("select review.id as id,a_account.name as teacher,title,body,date,check_flg,read_flg,comment from review inner join a_account on teacher=a_account.id where read_flg=0 and student=%s order by date asc",student_id)
    
    return render_template("u_check_home.html",read=read,unread=unread)

@app.route("/u_check/detail")
def u_check_detail():
    dbmg = db_manager()

    id = request.args.get("id")
    check = dbmg.exec_query("select review.id as id,a_account.name as teacher,title,body,date,check_flg,read_flg,comment from review inner join a_account on teacher=a_account.id where review.id=%s",id)

    return render_template("u_check_detail.html",check=check[0])

@app.route("/u_check/request")
def u_check_request():
    dbmg = db_manager()
    teachers = dbmg.exec_query("select id,name from a_account where public_flg=1")
    return render_template("u_check_1.html",teachers=teachers)

@app.route("/u_check/confirm",methods=["POST"])
def u_check_confirm():
    dbmg = db_manager()

    teacher_id = request.form.get("teacher")
    date = request.form.get("date")
    title = request.form.get("title")
    body = request.form.get("body")

    # 未入力の項目がある場合
    if not (teacher_id and date and title and body):
        return redirect(url_for('u_check_request'))

    # 日付が過去の場合
    date_check = datetime.datetime.strptime(date, '%Y-%m-%d')
    today = datetime.date.today()
    if date_check.date() < today:
        return redirect(url_for('u_check_request'))

    # タイトルの文字数が長すぎる場合
    if len(title) > 32:
        return redirect(url_for('u_check_request'))

    # 本文の文字数が長すぎる場合
    if len(body) > 600:
        return redirect(url_for('u_check_request'))

    teacher = dbmg.exec_query("select id,name from a_account where id=%s",teacher_id)

    check = {
        "teacher":teacher[0],
        "date":request.form.get("date"),
        "title":request.form.get("title"),
        "body":request.form.get("body")
    }

    return render_template("u_check_2.html",check=check)

@app.route("/u_check/done",methods=["POST"])
def u_check():
    dbmg = db_manager()

    check = (
        session["id"],
        request.form.get("id"),
        request.form.get("title"),
        request.form.get("body"),
        request.form.get("date")
    )

    dbmg.exec_query("insert into review(student,teacher,title,body,date) values(%s,%s,%s,%s,%s)",check)

    return render_template("u_check_3.html")

@app.route("/u_search")
def u_search_page():
    explanation_flg = "true"

    years = []
    for a in glob.glob('./static/pdf/*/'):
        years.append([a[13:17]])
    # 年度を新しい順（降順）にする
    years.sort(reverse=True)

    return render_template("u_search.html",years=years,explanation_flg=explanation_flg)

@app.route("/u_search/result")
def u_search():
    name = request.args.get("name")
    year = request.args.get("year")
    if not name:
        name = "*"
    if not year:
        year = "*"

    results = []
    for a in glob.glob('./static/pdf/' + year + '/*' + name + '*.pdf'):
        result = a.replace("\\","/")[9:]
        filename = result[9:]
        results.append([result,filename])

    years = []
    for a in glob.glob('./static/pdf/*/'):
        years.append([a[13:17]])
    # 年度を新しい順（降順）にする
    years.sort(reverse=True)

    return render_template("u_search.html",results=results,years=years)

@app.route("/u_forum",methods=["GET","POST"])
def u_forum_page():
    dbmg = db_manager()

    word = "%"
    search_flg = False

    if request.method == "POST":
        word = "%" + request.form.get("word") + "%"
        search_flg = True

    threads = dbmg.exec_query("select * from threads where title like %s order by last_update desc",word)

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("u_forum.html",threads=threads,search_flg=search_flg)

@app.route("/u_account")
def u_account_page():
    grad_years,deps = get_classes()
    return render_template("u_account_1.html",deps=deps,grad_years=grad_years)

@app.route("/u_account/confirm",methods=["POST"])
def u_account_confirm():
    dbmg = db_manager()

    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year = request.form.get("grad_year")
    dep = request.form.get("dep")

    # 未入力の項目がある場合
    if not (id and pw and name and grad_year and dep):
        return redirect(url_for("u_account_page"))

    # pwの文字数が不正な場合
    if len(pw) < 8 or len(pw) > 20:
        return redirect(url_for("u_account_page"))

    # nameの文字数が不正な場合
    if len(name) > 16:
        return redirect(url_for("u_account_page"))

    dep = dbmg.exec_query("select * from dep where id=%s",dep)[0]

    account = {
        "id":id,
        "pw":pw,
        "name":name,
        "grad_year":grad_year,
        "dep":dep
    }

    return render_template("u_account_2.html",account=account)

@app.route("/u_account/done",methods=["POST"])
def u_account():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year = request.form.get("grad_year")
    dep_id = request.form.get("dep")

    hash_pw,salt = dbmg.calc_pw_hash(pw)
    class_id = grad_year + dep_id

    dbmg.exec_query("update u_account set hash_pw=%s,salt=%s,name=%s,class_id=%s where id=%s",(hash_pw,salt,name,class_id,id))

    return render_template("u_account_3.html")

# 管理者の処理 -------------------------------------------------------------------

@app.route("/a_login")
def a_login_page():
    return render_template("a_login.html")

@app.route("/a_login",methods=["POST"])
def a_login():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    
    # 入力された id が存在しない場合
    user = dbmg.exec_query("select * from a_account where id=%s",id)
    if len(user) == 0:
        return redirect("/a_login")

    hash_pw,_ = dbmg.calc_pw_hash(pw,user[0]["salt"])

    if hash_pw == user[0]["hash_pw"]:
        session["id"] = user[0]["id"]
        session["user"] = "admin"
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(hours=168) # 定数？
        return redirect("/a_home")
    else:
        return redirect("/a_login") 

@app.route("/a_home")
def a_home_page():
    dbmg = db_manager()

    if "id" not in session:
        return redirect("/")
    
    id = session["id"]
    today = str(datetime.date.today())
    date_max = str(datetime.date.today() + datetime.timedelta(7))
    date_time_min = today + " " + "00:00:00"
    date_time_max = date_max + " " + "23:59:59"
    
    # notification.notify(
    #     title="予定",
    #     message="選考予定の生徒がいます",
    #     app_name="JBRecluit",
    #     app_icon="static/img/favicon.ico",
    #     timeout=10
    # )

    # 直近の選考予定
    sql = "select u_account.id as id,name,company,date_time,step,detail from schedule join u_account on schedule.id = u_account.id where class_id in (select class_id from teacher_class where id = %s) and date_time >= %s and date_time <= %s order by date_time asc"
    schedules = dbmg.exec_query(sql,(id,date_time_min,date_time_max))

    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]
    
    # 面接練習
    sql = "select id,date,comment from practice where teacher = %s and date >= %s and carrying_out_flg = %s order by date asc"
    practices = dbmg.exec_query(sql,(id,today,True))
    
    # 文章チェック
    sql = "select review.id as id,name,title from review join u_account on student = u_account.id where teacher = %s and check_flg = 0 order by date asc"
    reviews = dbmg.exec_query(sql,(id))
    
    # 担当クラスの生徒の中で、内定済みの企業が1社以上ある生徒の人数を取得
    sql = "select count(distinct(schedule.id)) as cnt from schedule join u_account on schedule.id = u_account.id where passed_flg = 1 and class_id in (select class_id from teacher_class where id = %s)"
    passed = dbmg.exec_query(sql,id)[0]["cnt"]

    # 担当クラスの生徒の中で、内定済みの企業が1社もない生徒の人数を取得
    sql = "select count(distinct(schedule.id)) as cnt from schedule join u_account on schedule.id = u_account.id where class_id in (select class_id from teacher_class where id = %s)"
    sum = dbmg.exec_query(sql,id)[0]["cnt"]

    # 内定率の計算（小数第1位まで）
    if sum == 0:
        percent = 0
    else:
        percent = round(passed / sum * 100,1)
    
    # 掲示板
    sql = "select * from threads order by last_update desc limit 3"
    threads = dbmg.exec_query(sql)

    for thread in threads:
        # コメント数の要素を追加
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]
    
    return render_template("a_home.html",schedules=schedules,practices=practices,reviews=reviews,passed=passed,sum=sum,threads=threads,percent=percent)
    
@app.route("/a_all")
def a_all_page():
    dbmg = db_manager()

    teacher_id = session["id"]

    passed_students_id = dbmg.exec_query("select id from u_account where class_id in (select class_id from teacher_class where id=%s) and id in (select distinct(id) from schedule where passed_flg=1)",teacher_id)
    passed_students = []
    for student in passed_students_id:
        # 学生の情報を取得
        passed_student = dbmg.exec_query("select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account inner join class on class_id=class.id inner join dep on dep_id=dep.id where u_account.id=%s",student["id"])
        # 受験済みの企業数を取得
        company_num = dbmg.exec_query("select count(distinct(company)) as company_num from schedule where id=%s",student["id"])
        # 企業数の属性を追加
        passed_student[0]["company_num"] = company_num[0]["company_num"]
        # 配列に追加
        passed_students.append(passed_student[0])

    unpassed_students_id = dbmg.exec_query("select id from u_account where class_id in (select class_id from teacher_class where id=%s) and id not in (select distinct(id) from schedule where passed_flg=1)",teacher_id)
    unpassed_students = []
    for student in unpassed_students_id:
        # 学生の情報を取得
        unpassed_student = dbmg.exec_query("select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account inner join class on class_id=class.id inner join dep on dep_id=dep.id where u_account.id=%s",student["id"])
        # 受験済みの企業数を取得
        company_num = dbmg.exec_query("select count(distinct(company)) as company_num from schedule where id=%s",student["id"])
        # 企業数の属性を追加
        unpassed_student[0]["company_num"] = company_num[0]["company_num"]
        # 配列に追加
        unpassed_students.append(unpassed_student[0])

    return render_template("a_all.html",passed_students=passed_students,unpassed_students=unpassed_students)

@app.route("/a_student")
def a_student_page():
    dbmg = db_manager()

    id = request.args.get("id")

    sql = "select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account join class on class_id = class.id join dep on dep_id = dep.id where u_account.id = %s"
    student = dbmg.exec_query(sql,id)

    # 選考中の企業
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and finished_flg = 0 and passed_flg = 0 order by date_time asc;"
    schedules = dbmg.exec_query(sql,(id,id))
    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]
    
    # 内定済みの企業
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and passed_flg = 1 order by date_time asc;"
    passed = dbmg.exec_query(sql,(id,id))
    
    # 落選済みの企業
    sql = "select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where id = %s and s1.company = s2.company group by company) and finished_flg = 1 order by date_time asc;"
    finished = dbmg.exec_query(sql,(id,id))
    
    return render_template("a_student.html",student=student[0],schedules=schedules,passed=passed,finished=finished)

@app.route("/a_company")
def a_company_page():
    dbmg = db_manager()

    id = request.args.get("id")
    company = request.args.get("company")
    state = request.args.get("state")

    sql = "select * from schedule where id = %s and company = %s order by date_time desc"
    schedules = dbmg.exec_query(sql,(id,company))

    sql = "select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account join class on class_id = class.id join dep on dep_id = dep.id where u_account.id = %s"
    student = dbmg.exec_query(sql,id)

    for schedule in schedules:
        # "YY-MM-DD hh:mm:ss" を "MM/DD hh:mm" に変更
        schedule["date_time"] = str(schedule["date_time"]).replace("-","/")[5:16]

    return render_template("a_company.html",schedules=schedules,student=student[0],state=state)

@app.route("/a_forum",methods=["GET","POST"])
def a_forum_page():
    dbmg = db_manager()

    word = "%"
    search_flg = False
    
    if request.method == "POST":
        word = "%" + request.form.get("word") + "%"
        search_flg = True

    threads = dbmg.exec_query("select * from threads where title like %s order by last_update desc",word)

    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]

    return render_template("a_forum.html",threads=threads,search_flg=search_flg)

@app.route("/a_practice")
def a_practice_home():
    dbmg = db_manager()

    teacher = session["id"]
    today = datetime.date.today()

    practices = dbmg.exec_query("select * from practice where carrying_out_flg = %s and teacher = %s and date >= %s order by date asc",(True,teacher,today))
    for practice in practices:
        num = dbmg.exec_query("select count(*) as num from practice_attendance where schedule_id = %s",practice["id"])
        num = num[0]["num"]
        practice["num"] = num

    return render_template("a_practice_home.html",practices=practices)

@app.route("/a_practice/create")
def a_practice_create():
    return render_template("a_practice_1.html")

@app.route("/a_practice/confirm",methods=["POST"])
def a_practice_confirm():
    date = request.form.get("date")
    comment = request.form.get("comment")

    # dateの入力チェック
    if not date:
        return redirect(url_for("a_practice_create"))

    # commentの入力チェック
    if not comment or len(comment) > 200:
        return redirect(url_for("a_practice_create"))

    date_check = datetime.datetime.strptime(date, '%Y-%m-%d')
    today = datetime.date.today()
    if date_check.date() < today:
        return redirect(url_for("a_practice_create"))

    return render_template("a_practice_2.html",date=date,comment=comment)

@app.route("/a_practice/done",methods=["POST"])
def a_practice():
    dbmg = db_manager()

    teacher = session["id"]
    date = request.form.get("date")
    comment = request.form.get("comment")

    dbmg.exec_query("insert into practice(teacher,date,comment) values(%s,%s,%s)",(teacher,date,comment))

    return render_template("a_practice_3.html")

@app.route("/a_practice/detail",methods=["GET","POST"])
def a_practice_detail():
    dbmg = db_manager()

    id = request.args.get("id")
    practice = dbmg.exec_query("select * from practice where id=%s",id)
    students = dbmg.exec_query("select u_account.name as name,dep.name as dep from practice_attendance inner join u_account on student=u_account.id inner join class on class_id=class.id join dep on dep_id=dep.id where schedule_id = %s",id)

    return render_template("a_practice_detail.html",practice=practice[0],students=students,num=len(students))

@app.route("/a_practice/modify",methods=["GET","POST"])
def a_practice_modify():
    dbmg = db_manager()

    if request.method == "GET":
        id = request.args.get("id")
        practice = dbmg.exec_query("select * from practice where id=%s",id)
        return render_template("a_practice_modify.html",practice=practice[0])

    id = request.form.get("id")
    practice = dbmg.exec_query("select * from practice where id=%s",id)

    comment = request.form.get("comment")
    if not comment or len(comment) > 200:
        return render_template("a_practice_modify.html",practice=practice[0])

    dbmg.exec_query("update practice set comment=%s where id=%s",(comment,id))
    return redirect(url_for("a_practice_detail",id=id))

@app.route("/a_practice/delete/confirm")
def a_practice_delete_confirm():
    dbmg = db_manager()

    id = request.args.get("id")
    practice = dbmg.exec_query("select * from practice where id=%s",id)
    students = dbmg.exec_query("select u_account.name as name,dep.name as dep from practice_attendance inner join u_account on student=u_account.id inner join class on class_id=class.id inner join dep on dep_id=dep.id where schedule_id=%s",id)

    return render_template("a_practice_delete_1.html",practice=practice[0],students=students,num=len(students))

@app.route("/a_practice/delete/done")
def a_practice_delete():
    dbmg = db_manager()

    id = request.args.get("id")
    dbmg.exec_query("update practice set carrying_out_flg=%s where id=%s",(False,id))

    return render_template("a_practice_delete_2.html")

@app.route("/a_check")
def a_check_home():
    dbmg = db_manager()

    id = session["id"]
    today = datetime.date.today()

    # チェック済みは提出期限前のものだけ選択
    checked = dbmg.exec_query("select review.id as id,u_account.name as name,title,date,check_flg from review inner join u_account on student = u_account.id where check_flg=1 and teacher=%s and date>=%s order by date asc",(id,today))
    # 未チェックは提出期限を過ぎたのものも含めて選択
    unchecked = dbmg.exec_query("select review.id as id,u_account.name as name,title,date,check_flg from review inner join u_account on student = u_account.id where check_flg=0 and teacher=%s order by date asc",id)

    return render_template("a_check_home.html",checked=checked,unchecked=unchecked)

@app.route("/a_check/detail",methods=["GET","POST"])
def a_check_detail():
    dbmg = db_manager()

    if request.method == "GET":
        id = request.args.get("id")
    
    if request.method == "POST":
        id = request.form.get("id")
        comment = request.form.get("comment")

        # 入力チェック
        if not comment or len(comment) > 300:
            return redirect(url_for("a_check_detail",id=id))

        dbmg.exec_query("update review set comment=%s,check_flg=1,read_flg=0 where id=%s",(comment,id))

        # コメントを更新したら文章チェックTOPに遷移する
        return redirect("/a_check")
        
    result = dbmg.exec_query("select review.id as id,u_account.name as name,title,body,date,check_flg,comment from review inner join u_account on student = u_account.id where review.id=%s",id)
    return render_template("a_check_detail.html",result=result[0])

@app.route("/a_thread")
def a_thread_page():
    dbmg = db_manager()

    id = request.args.get("id")
    thread = dbmg.exec_query("select * from threads where id = %s",id)

    num = dbmg.exec_query("select count(*) as num from comments where thread_id = %s",id)
    thread[0]["num"] = num[0]["num"]

    return render_template("a_thread_1.html",thread=thread[0])

@app.route("/a_thread/done")
def a_thread_delete():
    dbmg = db_manager()

    id = request.args.get("id")

    dbmg.exec_query("delete from threads where id = %s",id)
    dbmg.exec_query("delete from comments where thread_id = %s",id)

    return render_template("a_thread_2.html")

@app.route("/a_user_account",methods=["GET","POST"])
def a_user_account_page():
    dbmg = db_manager()

    grad_years,deps = get_classes()

    if request.method == "GET":
        return render_template("a_user_account_1.html",deps=deps,grad_years=grad_years)
    
    id = request.form.get("id")
    grad_year = request.form.get("grad_year")
    dep = request.form.get("dep")
    name = request.form.get("name")

    if id:
        users = dbmg.exec_query("select u_account.id as id,u_account.name as name,graduation as grad_year,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where u_account.id = %s",id)
    else:
        # DBで検索するために変形
        if grad_year != None:
            grad_year = grad_year + "%"
        if dep != None:
            dep = "%" + dep
        if name != None:
            name = "%" + name + "%"

        users = dbmg.exec_query("select u_account.id as id,u_account.name as name,graduation as grad_year,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where class_id like %s and class_id like %s and u_account.name like %s",(grad_year,dep,name))

    return render_template("a_user_account_1.html",deps=deps,grad_years=grad_years,users=users)

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
    dbmg = db_manager()

    id = request.args.get("id")
    dbmg.exec_query("delete from u_account where id = %s",id)

    return render_template("a_user_account_3.html")

@app.route("/a_account")
def a_account_page():
    id = session["id"]
    grad_years,deps = get_classes()
    return render_template("a_account_1.html",id=id,deps=deps,grad_years=grad_years)

@app.route("/a_account/confirm",methods=["POST"])
def a_account_confirm():
    dbmg = db_manager()

    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")
    published = request.form.get("published")

    # 未入力の項目がある場合
    if not (pw and name and grad_year1 and dep1 and grad_year2 and dep2):
        return redirect(url_for("a_account_page"))

    # pw の入力チェック
    if len(pw) < 8 or len(pw) > 20:
        return redirect(url_for("a_account_page"))

    # name の入力チェック
    if len(name) > 16:
        return redirect(url_for("a_account_page"))

    # 担当クラスの入力チェック
    if grad_year1 == grad_year2 and dep1 == dep2:
        return redirect(url_for("a_account_page"))

    dep1 = dbmg.exec_query("select * from dep where id=%s",dep1)[0]
    if grad_year2 and dep2:
        dep2 = dbmg.exec_query("select * from dep where id=%s",dep2)[0]
    else:
        grad_year2 = None
        dep2 = None

    account = {
        "id":id,
        "pw":pw,
        "name":name,
        "grad_year1":grad_year1,
        "dep1":dep1,
        "grad_year2":grad_year2,
        "dep2":dep2,
        "published":published
    }

    return render_template("a_account_2.html",account=account)

@app.route("/a_account/done",methods=["POST"])
def a_account():
    dbmg = db_manager()

    id = session["id"]
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")
    published = request.form.get("published")

    if published == "true":
        published = True
    elif published == "false":
        published = False

    hash_pw, salt = dbmg.calc_pw_hash(pw)

    dbmg.exec_query("update a_account set hash_pw=%s, salt=%s, name=%s, public_flg=%s where id=%s",(hash_pw,salt,name,published,id))
    dbmg.exec_query("delete from teacher_class where id = %s",id)
    
    class_id1 = grad_year1 + dep1
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))

    if grad_year2 and dep2:
        class_id2 = grad_year2 + dep2
        dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id2))

    return render_template("a_account_3.html")

@app.route("/a_signup")
def a_signup_page():
    grad_years,deps = get_classes()
    return render_template("a_signup_1.html",deps=deps,grad_years=grad_years)

@app.route("/a_signup/confirm",methods=["POST"])
def a_signup_confirm():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")
    published = request.form.get("published")

    # 未入力の項目がある場合
    if not (id and pw and name and grad_year1 and dep1 and published):
        return redirect(url_for("a_signup_page"))

    # idが既に使われている場合
    id_check = dbmg.exec_query("select * from a_account where id=%s",id)
    if len(id_check) != 0:
        return redirect(url_for("a_signup_page"))

    # pw の入力チェック
    if len(pw) < 8 or len(pw) > 20:
        return redirect(url_for("a_signup_page"))

    # name の入力チェック
    if len(name) > 16:
        return redirect(url_for("a_signup_page"))

    # 担当クラスの入力チェック
    if grad_year1 == grad_year2 and dep1 == dep2:
        return redirect(url_for("a_account_page"))

    dep1 = dbmg.exec_query("select * from dep where id=%s",dep1)[0]
    if grad_year2 and dep2:
        dep2 = dbmg.exec_query("select * from dep where id=%s",dep2)[0]
    else:
        grad_year2 = None
        dep2 = None

    account = {
        "id":id,
        "pw":pw,
        "name":name,
        "grad_year1":grad_year1,
        "dep1":dep1,
        "grad_year2":grad_year2,
        "dep2":dep2,
        "published":published
    }

    return render_template("a_signup_2.html",account=account)

@app.route("/a_signup/done",methods=["POST"])
def a_signup():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    name = request.form.get("name")
    grad_year1 = request.form.get("grad_year1")
    dep1 = request.form.get("dep1")
    grad_year2 = request.form.get("grad_year2")
    dep2 = request.form.get("dep2")
    published = request.form.get("published")

    if published == "true":
        published = True
    elif published == "false":
        published = False
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    dbmg.exec_query("insert into a_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,published))

    class_id1 = grad_year1 + dep1
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))

    if grad_year2 and dep2:
        class_id2 = grad_year2 + dep2
        dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id2))

    return render_template("a_signup_3.html")

# 利用者・管理者で共通の処理 ------------------------------------------------------

@app.route("/logout")
def logout():
    # セッションを空にする
    if "id" in session:
        session.pop("id",None)
        session.pop("user",None)
    
    return redirect("/")

@app.route("/forum_build")
def forum_build_page():
    user = request.args.get("user")
    return render_template("forum_build.html",user=user)

@app.route("/forum_build/done",methods=["POST"])
def forum_build():
    dbmg = db_manager()

    id = session["id"]
    date_time = datetime.datetime.now()

    user = request.form.get("user")
    title = request.form.get("title")
    body = request.form.get("body")

    # タイトルの入力チェック
    if not title or len(title) > 30:
        return redirect(url_for('forum_build_page',user=user))
    
    # 本文の入力チェック
    if not body or len(body) > 500:
        return redirect(url_for('forum_build_page',user=user))

    if user == "user":
        name = dbmg.exec_query("select name from u_account where id = %s",id)
        name = name[0]["name"]
    elif user == "admin":
        name = dbmg.exec_query("select name from a_account where id = %s",id)
        name = name[0]["name"]
    else:
        return redirect(url_for('forum_build_page',user=user))
    
    dbmg.exec_query("insert into threads(title,author_id,author,last_contributer_id,last_contributer,last_update) values(%s,%s,%s,%s,%s,%s)",(title,id,name,id,name,date_time))
    
    # thread_id の取得方法はこれでいいのか？修正検討
    thread_id = dbmg.exec_query("select id from threads where author_id=%s order by last_update desc limit 1",id)
    thread_id = thread_id[0]["id"]

    dbmg.exec_query("insert into comments(thread_id,contributer_id,contributer,date_time,body) values(%s,%s,%s,%s,%s)",(thread_id,id,name,date_time,body))

    return redirect(url_for("forum_brows",thread_id=thread_id,user=user))

@app.route("/forum_brows")
def forum_brows():
    dbmg = db_manager()

    thread_id = request.args.get("thread_id")
    user = request.args.get("user")
    
    thread = dbmg.exec_query("select * from threads where id = %s",thread_id)
    comments = dbmg.exec_query("select * from comments where thread_id = %s",thread_id)

    return render_template("forum_brows.html",thread=thread[0],comments=comments,user=user)

@app.route("/forum_contribute",methods=["POST"])
def forum_contribute():
    dbmg = db_manager()

    id = session["id"]
    thread_id = request.form.get("thread_id")
    user = request.form.get("user")
    body = request.form.get("body")
    date_time = datetime.datetime.now()

    # 入力チェック
    if not body or len(body) > 500:
        return redirect(url_for("forum_brows",thread_id=thread_id,user=user))

    # 名前の取得
    if user == "user":
        name = dbmg.exec_query("select name from u_account where id = %s",id)
        name = name[0]["name"]
    elif user == "admin":
        name = dbmg.exec_query("select name from a_account where id = %s",id)
        name = name[0]["name"]
    else:
        return redirect(url_for("forum_brows",thread_id=thread_id,user=user))
    
    # コメントの記録
    dbmg.exec_query("insert into comments(thread_id,contributer_id,contributer,date_time,body) values(%s,%s,%s,%s,%s)",(thread_id,id,name,date_time,body))
    dbmg.exec_query("update threads set last_contributer_id = %s,last_contributer = %s where id = %s",(id,name,thread_id))

    return redirect(url_for("forum_brows",thread_id=thread_id,user=user))

# -------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)