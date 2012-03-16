#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

import ConfigParser
import argparse

conffile = "/etc/tsqauth/config.cfg"                                                     
cur = None                                                                               
con = None

def cmd_twi_login(name):
    pass

def main():
    global con, cur
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(conffile))
        # коннектимся к бд, создаем таблицу, если её не существует
        con = sqlite3.connect(config.get("sql_auth", "users"))
        cur = con.cursor()
        cur.execute("""
        create table if not exists users
        (
            username    varchar(32) NOT NULL primary key collate nocase,
            password    varchar(32) NOT NULL
        )""")
        con.commit()

    except IOError as e:
        print "Cannot open config file:", e
    except sqlite3.OperationalError as e:
        print "Sql error:", e
    except ImportError:
        pass
    finally:
        # закрываем бд
        if cur is not None: cur.close()
        if cur is not None: con.close()

if __name__=="__main__":
    main()
