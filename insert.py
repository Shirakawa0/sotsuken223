from pymysql import IntegrityError
from db.db_manager import db_manager

dbmg = db_manager()

# 学科・学年・クラスに変更・追加があった場合は入力し、実行 --------------------------

# 学科を入力
dep = {
    "01":"情報システム科",
    "02":"ネットワークセキュリティ科",
    "03":"総合システム工学科",
    "04":"高度情報工学科",
    "05":"情報ビジネス科",
    "06":"総合デザイン科",
    "07":"グラフィックデザインコース",
    "08":"アニメ・マンガコース",
    "09":"CGクリエイトコース",
    "10":"建築インテリアコース",
}
grades = ["1","2","3","4"] # 学年を入力
classes = ["1","2","3"] # クラスを入力

# これより下は原則変更しないこと ---------------------------------------------------

# depテーブルに登録
for i in range(len(dep)):
    id = list(dep.keys())
    name = list(dep.values())
    try:
        dbmg.exec_query("insert into dep values(%s,%s)",(id[i],name[i]))
    except IntegrityError:
        continue

dep_ids = dep.keys()

# classテーブルに登録
for dep_id in dep_ids:
    for grade in grades:
        for Class in classes:
            class_id = dep_id + grade + Class
            try:
                dbmg.exec_query("insert into class values(%s,%s,%s,%s)",(class_id,dep_id,grade,Class))
            except IntegrityError:
                pass