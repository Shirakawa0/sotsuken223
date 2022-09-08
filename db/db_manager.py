# データベース操作クラス

import pymysql.cursors
# import pymysql
import random,string,hashlib

class db_manager():
    
    def connect(self):

        # DB接続
        return pymysql.connect(
            host="localhost",
            user="root",
            password="shirakawa",
            db="book",
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor # Dict(辞書型)で受け取る
        )

    def exec_query(self,sql,params=()):
        # DB検索
        with self.connect() as conn: # DB接続（上の関数を使う）
            with conn.cursor() as cursor: # カーソル設置
                cursor.execute(sql,params) # SQL実行
                results = cursor.fetchall() # 結果取得（すべて取得）
            conn.commit()
        return results

    def calc_pw_hash(self,pw,salt="".join(random.choices(string.ascii_letters, k=5))):
            # ハッシュ処理
            # 1. エンコード UTF-8
            pw_salt = (pw + salt).encode("UTF-8")
            # 2. ハッシュ化 SHA512
            hash_pw = hashlib.sha512(pw_salt).hexdigest()
            # 3. ハッシュ値とソルトを返す
            return hash_pw,salt