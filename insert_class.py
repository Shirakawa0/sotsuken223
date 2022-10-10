from pymysql import IntegrityError
from db.db_manager import db_manager

dbmg = db_manager()

# 学科・学年・組を追加するときは
# 以下3つの配列に要素を追加して実行（すべて文字列）
# dep:学科ID / grade:学年 / class:組
dep = ["01","02","03","04"]
grade = ["1","2","3","4"]
Class = ["1","2","3"]

for d in dep:
    for g in grade:
        for c in Class:
            class_id = d + g + c
            try:
                dbmg.exec_query("insert into class values(%s,%s,%s,%s)",(class_id,d,g,c))
            except IntegrityError:
                pass