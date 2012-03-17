#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

import sys # sys.exit
import argparse

try:
    import configparser # python3
except ImportError:
    import ConfigParser as configparser # python2

import hashlib # md5 hash
import base64
conffile = "/etc/tsqauth/config.cfg"
cur = None
con = None
encoding = None

def error(*e):
    l = list(e)
    l.insert(0, "Error:")
    print(" ".join(l))

# выдает md5 хэш строки
def passwd(p):
    m = hashlib.md5()
    m.update(p.encode(encoding))
    return base64.b64encode(m.digest())

# выводит список всех пользователей с хешами паролей
def list_users():
    global con, cur
    cur.execute("select username,password from users")
    result = cur.fetchall()
    for x, y in result:
        print("".join(["User: ", x, " md5: ", y]))

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
    if cur.rowcount > 0:
        print("".join(["User \"", user, "\" deleted"]))
    else:
        print("".join(["User \"", user, "\" not found"]))
    con.commit()

def main():
    global con, cur, encoding
    try:
        
        config = configparser.ConfigParser()
        config.readfp(open(conffile))
        encoding = config.get("global", "encoding")

        # коннектимся к бд, создаем таблицу, если её не существует
        con = sqlite3.connect(config.get("sql_auth", "users"), 10) # timeout 10
        cur = con.cursor()

        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--password", action="store")
        parser.add_argument("-u", "--user", action="store")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add", action='store_true', help="Add user")
        group.add_argument("-l", "--list", action='store_true', help="List users (default)")
        group.add_argument("-d", "--delete", action='store_true', help="Delete user")

        args = parser.parse_args()
       
        user = args.user
        password = args.password

        if args.add:
            if (user is not None) and (password is not None):
                add(user.decode(encoding).lower(), password.decode(encoding))
            else:
                error("need username and password")
                sys.exit(2)
        elif args.delete:
            if (user is not None):
                delete(user.decode(encoding).lower())
            else:
                error("need username")
                sys.exit(2)
        else:
            list_users()
   

    except IOError as e:
        error("Cannot open config file:", str(e))
    except sqlite3.OperationalError as e:
        error(str(e))

    except ImportError:
        pass
    finally:
        # закрываем бд
        if cur is not None: cur.close()
        if cur is not None: con.close()

if __name__=="__main__":
    main()

