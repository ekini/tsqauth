#!/usr/bin/env python

import os
import time
import sys  # sys.exit(), sys.stdout.flush()
import argparse

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

try:
    import configparser  # python3
except ImportError:
    import ConfigParser as configparser  # python2

from tsqauth import error  # functions
from tsqauth import conffile  # variables


def main():
    config = configparser.ConfigParser()
    config.readfp(open(conffile))

    # connect to database with 10 sec timeout
    con = sqlite3.connect(config.get("sql", "session_db"), 10)
    con.text_factory = str
    cur = con.cursor()

    while (1):
        # remove trailing characters from string
        ip = sys.stdin.readline().strip()

        # delete old entries
        cur.execute("delete from addresses where end_time<(?)",
                    (int(time.time()), ))
        con.commit()
        cur.execute("select user from addresses where ip=(?)", (ip, ))
        result = cur.fetchone()
        if result:
            # ok reply for squid with username
            print("OK user=%s" % result)
            sys.stdout.flush()
        else:
            print("ERR")
            sys.stdout.flush()
    cur.close()
    con.close()

if __name__ == "__main__":
    main()
