#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-04-08 16:08:57
# @Author  : mx (spring_chu@sjtu.edu.cn)
# @Link    : ${link}
# @Version : $Id$

import os
import MySQLdb
# 打开数据库连接
db = MySQLdb.connect("107.191.118.80","root","123456","twitter3" )

# 使用cursor()方法获取操作游标 
cursor = db.cursor()

# 使用execute方法执行SQL语句
cursor.execute("SELECT VERSION()")

# 使用 fetchone() 方法获取一条数据库。
data = cursor.fetchone()

print "Database version : %s " % data
print "1"
# 关闭数据库连接
db.close()