import pymysql,io
sql=io.open('platform-sql/018_menu_unify.sql',encoding='utf-8').read()
conn=pymysql.connect(host='192.168.31.153',port=33306,user='root',password='5677@Mysql',database='bp_platform_v2',charset='utf8mb4',autocommit=False,client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS)
try:
 cur=conn.cursor()
 cur.execute(sql)
 while cur.nextset(): pass
 conn.commit()
 print('migration committed')
 cur.execute("select count(*) from bp_menu where scene_code='GUARANTEE' and menu_type='PAGE'")
 print('pages',cur.fetchone()[0])
 cur.execute("select count(*) from bp_menu where scene_code='GUARANTEE' and menu_type='GROUP'")
 print('groups',cur.fetchone()[0])
 cur.execute("select count(*) from bp_role_menu rm join bp_menu m on m.id=rm.menu_id where m.menu_code like 'legacy_%'")
 print('legacy role menus',cur.fetchone()[0])
except Exception as e:
 conn.rollback(); print('FAILED',e); raise
finally:
 conn.close()
