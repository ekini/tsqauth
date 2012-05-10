#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: 2012, Eugene "ekini" Dementiev
# Author: Eugene "ekini" Dementiev (http://dementiev.eu)
# License: Beerware

import sys  # sys.exit
import argparse
from crypt import crypt
try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

try:
    import configparser  # python3
except ImportError:
    import ConfigParser as configparser  # python2

from tsqauth import error, getsalt, ispy3  # functions
from tsqauth import conffile  # variables

cur = None
con = None


# выводит список всех пользователей с хешами паролей
def list_users():
    global con, cur
    cur.execute("select username,password from users")
    result = cur.fetchall()
    for x, y in result:
        print("".join(["User: ", x, " md5: ", str(y)]))


# добавляет пользователя, если такого не существует
def add(user, password):
    global con, cur

    password = crypt(password, "".join(["$6$", getsalt()]))
    try:
        cur.execute("""INSERT INTO users
            (`username`, `password`) VALUES (?, ?)""", (user, password))
        con.commit()
    except sqlite3.IntegrityError as e:
        error(str(e))


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

        # коннектимся к бд, создаем таблицу, если её не существует
        # timeout 10 sec
        con = sqlite3.connect(config.get("sql_auth", "users"), 10)
        con.text_factory = str
        cur = con.cursor()

        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--password", action="store")
        parser.add_argument("-u", "--user", action="store")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add",
                    action='store_true', help="Add user")
        group.add_argument("-l", "--list",
                    action='store_true', help="List users (default)")
        group.add_argument("-d", "--delete",
                    action='store_true', help="Delete user")

        args = parser.parse_args()

        if args.add:
            if (args.user is not None) and (args.password is not None):
                add(args.user.lower(), args.password)
            else:
                error("need username and password")
                sys.exit(2)
        elif args.delete:
            if (args.user is not None):
                delete(args.user.lower())
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
        if cur is not None:
            cur.close()
        if cur is not None:
            con.close()

if __name__ == "__main__":
    main()
