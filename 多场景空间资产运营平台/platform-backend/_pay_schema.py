import pymysql
c=pymysql.connect(host='192.168.31.153',port=33306,user='root',password='5677@Mysql',database='bp_platform_v2',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor); cur=c.cursor(); cur.execute("show tables like '%payment%'"); print([list(x.values())[0] for x in cur.fetchall()]); c.close()
