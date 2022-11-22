from flask import Flask,render_template,request,redirect,url_for,session
import datetime
import random,string
import glob
from db.db_manager import db_manager

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

# 定数 --------------------------------------------------------------------------

SESSION_LIFETIME_MINUTES = 30

# 関数 --------------------------------------------------------------------------

def get_classes():
    dbmg = db_manager()

    this_year = datetime.date.today().year - 2000
    grad_years = [this_year + 1,this_year + 2, this_year + 3, this_year + 4]
    
    deps = dbmg.exec_query("select * from dep")

    return grad_years,deps

# 利用者の処理 ---------------------------------------------------------

@app.route("/")
def u_login_page():
    return render_template("u_login.html")

@app.route("/",methods=["POST"])
def u_login():
    dbmg = db_manager()

    id = request.form.get("id")
    pw = request.form.get("pw")
    
    account = dbmg.exec_query("select * from u_account where id=%s",id)

    # 入力された id が存在しない場合
    if len(account) == 0:
        return redirect("/")

    hash_pw,_ = dbmg.calc_pw_hash(pw,account[0]["salt"])

    if hash_pw == account[0]["hash_pw"]:
        session["id"] = account[0]["id"]
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=SESSION_LIFETIME_MINUTES)
        return redirect("/u_home")
    else:
        return redirect("/")

@app.route("/u_signup")
def u_signup_page():
    grad_years,deps = get_classes()
    return render_template("u_signup_1.html",grad_years=grad_years,deps=deps)

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
    
    # id の入力チェック
    ## 既に使われている場合
    id_check = dbmg.exec_query("select * from u_account where id=%s",id)
    if len(id_check) != 0:
        return redirect(url_for("u_signup_page"))
    
    ## 文字数が7文字でない場合
    if len(id) != 7:
        return redirect(url_for("u_signup_page"))

    ## 学籍番号が文字列の場合
    try:
        int(id)
    except ValueError:
        return redirect(url_for("u_signup_page"))

    ## 学籍番号が不正な場合
    if int(id) < 1000000:
        return redirect(url_for("u_signup_page"))

    # pw の入力チェックS
    ## 文字数が不正な場合
    if len(pw) < 8 or len(pw) > 20:
        return redirect(url_for("u_signup_page"))

    # name の入力チェック
    ## 文字数が不正な場合
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
    
    teachers = dbmg.exec_query("select id,name from a_account")

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

    id = request.args.get("id")
    dbmg.exec_query("delete from practice_attendance where schedule_id=%s",id)

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
    teachers = dbmg.exec_query("select id,name from a_account")
    return render_template("u_check_1.html",teachers=teachers)

@app.route("/u_check/confirm",methods=["POST"])
def u_check_confirm():
    dbmg = db_manager()

    teacher_id = request.form.get("teacher")
    date = request.form.get("date")
    title = request.form.get("title")
    body = request.form.get("body")

    # 入力チェック
    ## 未入力の項目がある場合
    if not (teacher_id and date and title and body):
        return redirect(url_for('u_check_request'))

    ## 日付が過去の場合
    date_check = datetime.datetime.strptime(date, '%Y-%m-%d')
    today = datetime.date.today()
    if date_check.date() < today:
        return redirect(url_for('u_check_request'))

    ## タイトルの文字数が長すぎる場合
    if len(title) > 32:
        return redirect(url_for('u_check_request'))

    ## 本文の文字数が長すぎる場合
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
    years = []
    for i,a in enumerate(glob.glob('./static/pdf/*/')):
        years.append([a[13:17]])
    return render_template("u_search.html",years=years)

@app.route("/u_search/u_search_res")
def u_search():
    name = request.args.get("name")
    year = request.args.get("year")
    results = []
    for i,a in enumerate(glob.glob('./static/pdf/'+year+'/*'+name+'*.pdf')):
        result = a.replace("\\","/")[9:]
        filename = result[9:]
        results.append([result,filename])
    years = []
    for i,a in enumerate(glob.glob('./static/pdf/*/')):
        years.append([a[13:17]])

    return render_template("u_search.html",results=results,years=years,name=name)


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

# 管理者の処理 -------------------------------------------------------------------

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
    late = str(datetime.date.today()+datetime.timedelta(30))
    date_time_s = date + " " + "00:00:00"
    date_time_e = late + " " + "23:59:59"
    
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
    sql = "select u_account.name as name,schedule.company as company,schedule.step as step,schedule.detail as detail,replace(substring(schedule.date_time,6,5),'-','/') as date_time from schedule left join u_account on schedule.id = u_account.id where date_time <= %s and date_time >= %s"
    schedules = dbmg.exec_query(sql,(date_time_e,date_time_s))
    sql = "select d.name as dep,b.name as name,right(date,5) as date from practice a,u_account b,class c,dep d where a.student = b.id and b.class_id = c.id and c.dep_id = d.id and a.teacher = %s"
    #面接練習
    sql = "select date,comment from practice where teacher = %s limit 3"
    practices = dbmg.exec_query(sql,(id))
    #文章チェック
    sql = "select b.name as student,a.title from review a,u_account b where a.student = b.id and a.teacher = %s and a.check_flg = 0 limit 3"
    reviews = dbmg.exec_query(sql,(id))
    #内定未内定
    sql = "select count(distinct b.id) as cnt from u_account a,schedule b where a.id = b.id and b.passed_flg = 1"
    passed = dbmg.exec_query(sql)
    sql = "select count(*) as cnt from u_account"
    sum = dbmg.exec_query(sql)
    # 掲示板
    sql = "select * from threads order by last_update desc limit 3"
    threads = dbmg.exec_query(sql)
    for thread in threads:
        comment_num = dbmg.exec_query("select count(id) as num from comments where thread_id = %s",thread["id"])
        thread["comment_num"] = comment_num[0]["num"]
   
    return render_template("a_home.html",schedules=schedules,practices=practices,reviews=reviews,passed=passed,sum=sum,threads=threads)
    
@app.route("/a_all")
def a_all_page():
    id = session["id"]
    class_id = request.args.get('class_id')

    dbmg = db_manager()
    classes = dbmg.exec_query("select class_id,cast(graduation as char) as grad_year,name as dep from teacher_class inner join class on class_id = class.id inner join dep on dep_id = dep.id where teacher_class.id=%s",id)
    if class_id:
        schedules = dbmg.exec_query("select schedule.id as id,name,cast(count(company) as char) as num from schedule inner join u_account on schedule.id = u_account.id where class_id = %s group by schedule.id",class_id)
        return render_template("a_all.html",classes=classes,schedules=schedules)
    else:
        return render_template("a_all.html",classes=classes)

@app.route("/a_student")
def a_student_page():
    id = request.args.get("id")

    dbmg = db_manager()
    student = dbmg.exec_query("select u_account.id as id,u_account.name as name,cast(graduation as char) as grad_year,dep.name as dep from u_account inner join class on class_id = class.id inner join dep on dep_id = dep.id where u_account.id=%s",id)
    schedules = dbmg.exec_query("select * from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and finished_flg = 0 and passed_flg = 0 order by date_time asc;",id)
    passed = dbmg.exec_query("select company from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and passed_flg = 1 order by date_time asc;",id)
    finished = dbmg.exec_query("select company from schedule as s1 where id = %s and date_time = (select max(date_time) from schedule as s2 where s1.company = s2.company group by company) and finished_flg = 1 order by date_time asc;",id)
    return render_template("a_student.html",student=student[0],schedules=schedules,passed=passed,finished=finished)

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

    practices = dbmg.exec_query("select * from practice where carrying_out_flg=%s and teacher=%s and date>=%s order by date asc",(True,teacher,today))
    for practice in practices:
        num = dbmg.exec_query("select count(*) as num from practice_attendance where schedule_id=%s",practice["id"])
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

    # 入力チェック
    if not date:
        return redirect(url_for("a_practice_create"))

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
    students = dbmg.exec_query("select u_account.name as name,dep.name as dep from practice_attendance inner join u_account on student=u_account.id inner join class on class_id=class.id inner join dep on dep_id=dep.id where schedule_id=%s",id)

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
    thread = dbmg.exec_query("select * from threads where id=%s",id)

    num = dbmg.exec_query("select count(*) as num from comments where thread_id=%s",id)
    thread[0]["num"] = num[0]["num"]

    return render_template("a_thread_1.html",thread=thread[0])

@app.route("/a_thread/done")
def a_thread_delete():
    id = request.args.get("id")

    dbmg = db_manager()
    dbmg.exec_query("delete from threads where id=%s",id)
    dbmg.exec_query("delete from comments where thread_id=%s",id)

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
    id = request.args.get("id")

    dbmg = db_manager()
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
    dep2 = dbmg.exec_query("select * from dep where id=%s",dep2)[0]

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

    class_id1 = grad_year1 + dep1
    class_id2 = grad_year2 + dep2

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    dbmg.exec_query("update a_account set hash_pw=%s, salt=%s, name=%s, public_flg=%s where id=%s",(hash_pw,salt,name,published,id))
    dbmg.exec_query("delete from teacher_class where id = %s",id)
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))
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
    if not (pw and name and grad_year1 and dep1 and published):
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
    dep2 = dbmg.exec_query("select * from dep where id=%s",dep2)[0]

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

    dbmg = db_manager()
    hash_pw, salt = dbmg.calc_pw_hash(pw)

    class_id1 = grad_year1 + dep1
    class_id2 = grad_year2 + dep2

    dbmg.exec_query("insert into a_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,published))
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id1))
    dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class_id2))

    return render_template("a_signup_3.html")

# 利用者・管理者で共通の処理 ------------------------------------------------------

@app.route("/logout")
def logout():
    if "id" in session:
        session.pop("id",None)   # セッションを空にする
    
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

    # 入力チェック
    ## タイトル
    if not title or len(title) > 30:
        return redirect(url_for('forum_build_page',user=user))
    ## 本文
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
    if not body or len(body) > 600:
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