from db.db_manager import db_manager

dbmg = db_manager()

id = "1"
pw = "1"
name = "サンフランシスコ"

hash_pw,salt = dbmg.calc_pw_hash(pw)
dbmg.exec_query("insert into a_account values(%s,%s,%s,%s,%s)",(id,hash_pw,salt,name,False))