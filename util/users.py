#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

import argparse
import sys # sys.exit
import locale

from argparse import ArgumentParser
import ConfigParser
import hashlib # md5 hash
import base64

conffile = "/etc/tsqauth/config.cfg"
cur = None
con = None

def error(e):
    print "Error:", e

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
    try:
        cur.execute("INSERT INTO users (`username`, `password`) VALUES (?, ?)", (user, password))
        con.commit()
    except sqlite3.IntegrityError as e:
        error(e)

# удаляет пользователя
def delete(user):
    global con, cur
    cur.execute("DELETE from users where username=?", (user,))
    print cur.rowcount
    con.commit()

def main():
    global con, cur
    try:
        
        print "c: ", locale.getpreferredencoding()
        config = ConfigParser.ConfigParser()
        config.readfp(open(conffile))
        # коннектимся к бд, создаем таблицу, если её не существует
        con = sqlite3.connect(config.get("sql_auth", "users"), 10) # timeout 10
        cur = con.cursor()

        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--password", action="store")
        parser.add_argument("-u", "--user", action="store")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add", action='store_true', help="Add user")
        group.add_argument("-l", "--list", action='store_true', help="List users")
        group.add_argument("-d", "--delete", action='store_true', help="Delete user")

        args = parser.parse_args()

        if args.add:
            if (args.user is not None) and (args.password is not None):
                add(args.user.decode(locale.getpreferredencoding()), args.password.decode(locale.getpreferredencoding()))
            else:
                error("need username and password")
                sys.exit(2)
        elif args.delete:
            if (args.user is not None):
                delete(args.user)
            else:
                error("need username")
                sys.exit(2)
        else:
            list_users()
   

    except IOError as e:
        print "Cannot open config file:", e
    except sqlite3.OperationalError as e:
        error(e)

    except ImportError:
        pass
    finally:
        # закрываем бд
        if cur is not None: cur.close()
        if cur is not None: con.close()

if __name__=="__main__":
    main()

