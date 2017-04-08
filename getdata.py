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
sql="select * from status"
conn=conn.query(sql)
