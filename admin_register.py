from db.db_manager import db_manager

dbmg = db_manager()

id = "test@morijyobi.ac.jp"
pw = "password"
name = "就活太郎"

hash_pw,salt = dbmg.calc_pw_hash(pw)
dbmg.exec_query("insert into a_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,False))