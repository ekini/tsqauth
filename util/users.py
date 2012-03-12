#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pysqlite2
from pysqlite2 import dbapi2 as sqlite3

import sys # sys.exit
import getopt # getopt
import hashlib # md5 hash
import base64

path="/usr/libexec/squidldapauth/users.db"

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
def list():
    global con, cur
    cur.execute("select * from users")
    result = cur.fetchall()
    for x, y in result:
        print "User:", x, "md5:", y

# добавляет пользователя, если такого не существует
def add(user,password):
    global con, cur
    password = passwd(password)
    if not get(user):
        cur.execute("INSERT INTO users (`username`, `password`) VALUES (\"%s\", \"%s\")" % (user, password))
        con.commit()
        print "User %s added" % user
    else:
        error("User exists")

# проверяет, существует ли пользователь в базе
def get(user):
    global con, cur
    cur.execute("SELECT * from users where username=\'%s\';" % user)
    if cur.fetchone():
        return 1

# удаляет пользователя
def delete(user):
    global con, cur
    if get(user):
        cur.execute("DELETE from users where username=\'%s\';" % user)
        con.commit()
        print "User %s deleted" % user
    else:
        error("User not found")

def main():
    global con, cur
    try:
        # коннектимся к бд, создаем таблицу, если её не существует
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("""
        create table if not exists users
        (
            username    varchar(32) NOT NULL,
            password    varchar(32) NOT NULL
        )""")
        con.commit()
        
        user = ""
        password = ""
        # man 3 getopt
        opts, args = getopt.getopt(sys.argv[1:], "adu:p:h")

        if not opts: list()

        for o, a in opts:
            if o == "-h":
                usage()
            elif o == "-u":
                user = a
            elif o == "-p":
                password = a
            elif o == "-d":
                if (user):
                    delete(user)
                else:
                    error("Enter username")
                break
            elif o == "-a":
                if (user and password):
                    add(user, passwd(password))
                else:
                    error("Enter username and password")
 
        # закрываем бд
        cur.close()
        con.close()
    except(pysqlite2.dbapi2.OperationalError) as e:
        print "Sql error:", e
    except getopt.GetoptError, err:
        print str(err) 
        usage()


if __name__=="__main__":
    main()

