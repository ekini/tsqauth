#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

try:
    import configparser  # python3
except ImportError:
    import ConfigParser as configparser  # python2

from tsqauth import error, conffile

cur = None
con = None


def main():
    global con, cur
    try:
        config = configparser.ConfigParser()
        config.readfp(open(conffile))

        con = sqlite3.connect(config.get("sql_auth", "users"))
        cur = con.cursor()
        try:
            cur.execute("""
            create table users
            (
                username    varchar(32) NOT NULL primary key collate nocase,
                password    varchar(100) NOT NULL
            )""")
            con.commit()
            print("Database \"users\" successfully created")
        except sqlite3.OperationalError:
            print("Database \"users\" is already created")

        cur.close()
        con.close()

        con = sqlite3.connect(config.get("sql", "session_db"))
        cur = con.cursor()
        try:
            cur.execute("""
            create table addresses
            (
                ip    varchar(15) NOT NULL,
                user  varchar(32) NOT NULL,
                start_time    uint(11) NOT NULL,
                end_time      uint(11) NOT NULL
    )""")
            con.commit()
            print("Database \"session_db\" successfully created")
        except sqlite3.OperationalError:
            print("Database \"session_db\" is already created")

    except IOError as e:
        error("Cannot open config file:", str(e))
    except sqlite3.OperationalError as e:
        error("(Sql)", str(e))
    except ImportError:
        pass
    finally:
        # закрываем бд
        if cur is not None:
            cur.close()
        if con is not None:
            con.close()

if __name__ == "__main__":
    main()
