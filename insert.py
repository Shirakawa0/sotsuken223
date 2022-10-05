from db.db_manager import db_manager

dbmg = db_manager()

dep = ["01","02","03","04"]
grade = ["1","2","3","4"]
Class = ["1","2","3"]

for d in dep:
    for g in grade:
        for c in Class:
            class_id = d + g + c
            dbmg.exec_query("insert into class values(%s,%s,%s,%s)",(class_id,d,int(g),int(c)))