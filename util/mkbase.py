#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

try:                                                                                     
    import configparser # python3
except ImportError:
    import ConfigParser as configparser # python2

conffile = "/etc/tsqauth/config.cfg"                                                     
cur = None                                                                               
con = None

def error(*e):
    l = list(e)
    l.insert(0, "Error:")
    print(" ".join(l))

def main():
    global con, cur
    try:
        config = configparser.ConfigParser()
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
        error("Cannot open config file:", str(e))
    except sqlite3.OperationalError as e:
        error("Sql error:", e)
    except ImportError:
        pass
    finally:
        # закрываем бд
        if cur is not None: cur.close()
        if cur is not None: con.close()

if __name__=="__main__":
    main()
