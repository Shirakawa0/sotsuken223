from db.db_manager import db_manager
from pymysql import IntegrityError

dbmg = db_manager()

id = "test@morijyobi.ac.jp"
pw = "password"
name = "就活太郎"
# 担当クラス1（必須・4桁のクラスIDを文字列で記述）
class1 = "2301"
# 担当クラス2（省略可・4桁のクラスIDを文字列で記述・省略する場合は None を設定）
class2 = "2504"
# class2 = None

hash_pw,salt = dbmg.calc_pw_hash(pw)

register_flg = True
try:
    dbmg.exec_query("insert into a_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,False))
except IntegrityError:
    register_flg = False
    print("そのIDはすでに使われています")

if register_flg:
    if class1:
        dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class1))
    if class2:
        dbmg.exec_query("insert into teacher_class values(%s,%s)",(id,class2))