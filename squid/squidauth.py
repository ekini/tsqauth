#!/usr/bin/env python

import os
import time
import sys # sys.exit(), sys.stdout.flush()
import argparse
from tsqauth import error, conffile

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

try:
    import configparser # python3
except ImportError:
    import ConfigParser as configparser # python2

error("blah")

def main():
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

if __name__=="__main__":
    main()
