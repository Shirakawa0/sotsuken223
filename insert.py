from pymysql import IntegrityError
from db.db_manager import db_manager
import datetime

dbmg = db_manager()

# 学科・学年・クラスに変更・追加があった場合は入力し、実行 --------------------------

# 学科を入力
dep = [
    ["01","情報システム科1組",2],
    ["02","情報システム科2組",2],
    ["03","総合システム工学科",3],
    ["04","高度情報工学科",4]
]

# これより下は原則変更しないこと ---------------------------------------------------

# depテーブルに登録
# for i in range(len(dep)):
#     id = list(dep.keys())
#     name = list(dep.values())
#     try:
#         dbmg.exec_query("insert into dep values(%s,%s)",(id[i],name[i]))
#     except IntegrityError:
#         continue

for d in dep:
    try:
        dbmg.exec_query("insert into dep values(%s,%s,%s)",(d[0],d[1],d[2]))
    except IntegrityError:
        continue

this_year = datetime.date.today().year
this_year2 = this_year - 2000
graduation_years = [this_year2 + 1,this_year2 + 2, this_year2 + 3, this_year2 + 4]

for g in graduation_years:
    for d in dep:  
        class_id = str(g) + d[0]
        try:
            dbmg.exec_query("insert into class values(%s,%s,%s)",(class_id,g,d[0]))
        except IntegrityError:
            pass

# dep_ids = dep.keys()

# classテーブルに登録
# for dep_id in dep_ids:
#     for grade in grades:
#         for Class in classes:
#             class_id = dep_id + grade + Class
#             try:
#                 dbmg.exec_query("insert into class values(%s,%s,%s,%s)",(class_id,dep_id,grade,Class))
#             except IntegrityError:
#                 pass