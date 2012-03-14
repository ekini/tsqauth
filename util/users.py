#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

import sys # sys.exit

from argparse import ArgumentParser
import ConfigParser
import hashlib # md5 hash
import base64

conffile = "/etc/squid-transparent-auth/config.cfg"

def error(e):
    print "Error:", e
def usage():
    print sys.argv[0], "[-u username] [-p password] [-a] [-d]"
    print """-a add user
-d delete user
-u username
-p password
    """
    sys.exit(2)
# выдает md5 хэш строки
def passwd(p):
    m = hashlib.md5()
    m.update(p)
    return base64.b64encode(m.digest())

# выводит список всех пользователей с хешами паролей
def list_users():
    global con, cur
    cur.execute("select username,password from users")
    result = cur.fetchall()
    for x, y in result:
        print "User:", x, "md5:", y

# добавляет пользователя, если такого не существует
def add(user,password):
    global con, cur
    password = passwd(password)
    if not get(user):
        cur.execute("INSERT INTO users (`username`, `password`) VALUES (?, ?)", (user, password))
        con.commit()
        print "User %s added" % user
    else:
        error("User exists")

# проверяет, существует ли пользователь в базе
def get(user):
    global con, cur
    cur.execute("SELECT * from users where username=?", user)
    if cur.fetchone():
        return 1

# удаляет пользователя
def delete(user):
    global con, cur
    if get(user):
        cur.execute("DELETE from users where username=?", user)
        con.commit()
        print "User %s deleted" % user
    else:
        error("User not found")

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
            username    varchar(32) NOT NULL,
            password    varchar(32) NOT NULL
        )""")
        con.commit()
       
        list_users()
    except IOError as e:
        print "Cannot open config file:", e
    except sqlite3.OperationalError as e:
        print "Sql error:", e
    except ImportError:
        pass
    finally:
        # закрываем бд
        cur.close()
        con.close()
if __name__=="__main__":
    main()

