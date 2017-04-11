#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-04-08 18:03:31
# @Author  : spring (spring_chu@sjtu.edu.cn)
# @Link    : ${link}
# @Version : $Id$

import os
from mysql import MySQL
conn = MySQL()
conn.selectDb('twitter3')
myhost = "107.191.118.80"
#myhost = "127.0.0.1"
myuser = "spring"
mypw = "123456"
sql_status="select distinct * from status"
results=conn.query(sql_status)
print results
res_stauts=conn.fetchAll()
follower_num1=0
for row in res_stauts:
    status_id = row['status_id']
    user_id = row['user_id']
    print user_id
    sql_follower="select * from follower where follower_id='%s'"%(user_id)
    print sql_follower
    follower_num=conn.query(sql_follower)
    follower_num1=follower_num1+follower_num
    print follower_num1
    #print status_id