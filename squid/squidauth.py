#!/usr/bin/env python

from pysqlite2 import dbapi2 as sqlite3
import os
import time
import sys

DB_FILE = "/usr/libexec/squidldapauth/ip.db"
log_file = "authsquid.log"
tries = 5

con = sqlite3.connect(DB_FILE)
cur = con.cursor()
cur.execute("""
        create table if not exists addresses
        (
          ip    varchar(15) NOT NULL,
          user  varchar(32) NOT NULL,
          start_time    uint(11) NOT NULL,
          end_time      uint(11) NOT NULL
        )
        """)
def failsafe_execute(query):
    for x in range(0,tries):
        try:
        cur.execute(query)
            break
        except sqlite3.OperationalError:
#            print ("Database is locked, retrying")
        time.sleep(1)
            pass 
while (1):
    # remove trailing characters from string
    ip = sys.stdin.readline().strip()

    # delete old entries
    failsafe_execute("delete from addresses where end_time<%s;" % time.time())
    con.commit()
    failsafe_execute("select * from addresses where ip=\'%s\';" % ip)
    result = cur.fetchone()
    if result:
        (ip, user, start_time, end_time) = result
    # ok reply for squid with username
        print "OK user=%s" % user 
    sys.stdout.flush()
    else:
        print "ERR"
        sys.stdout.flush()
cur.close()
con.close()
