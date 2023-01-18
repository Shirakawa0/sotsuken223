from pymysql import IntegrityError
from db.db_manager import db_manager
import datetime

dbmg = db_manager()

dep = [
    ["01","情報システム科1組",2],
    ["02","情報システム科2組",2],
    ["03","総合システム工学科",3],
    ["04","高度情報工学科",4]
]

for d in dep:
    try:
        dbmg.exec_query("insert into dep values(%s,%s,%s)",(d[0],d[1],d[2]))
    except IntegrityError:
        continue

this_year = datetime.date.today().year - 2000
graduation_years = [this_year,this_year + 1,this_year + 2, this_year + 3, this_year + 4]

for g in graduation_years:
    for d in dep:  
        class_id = str(g) + d[0]
        try:
            dbmg.exec_query("insert into class values(%s,%s,%s)",(class_id,g,d[0]))
        except IntegrityError:
            pass