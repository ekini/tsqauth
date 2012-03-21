#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
try:
    from urlparse import parse_qs  # Python 2
    from urllib import quote
except ImportError:
    from urllib.parse import parse_qs, quote  # Python 3

try:
    import ldap
except ImportError:
    pass
import os  # for os.environ
import sys
from crypt import crypt

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python2
try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

import time  # for time.sleep and time conversion functions
import datetime

from tsqauth import error, template, ispy3  # functions
from tsqauth import conffile, encoding

config = None

try:
    config = configparser.ConfigParser()
    config.readfp(open(conffile))
except IOError as e:
    error(str(e))


class Authentificator:
    def __init__(self):
        pass

    # общая функция аутентификации, вызывает auth_ldap или auth_sql
    # в зависимости от значения переменной "method"
    def auth(self, username, password):
        # если логин или пароль пустой, то выводим ошибку
        if not (username and password):
            return "Enter login and password"
        else:
            return ""


class AuthentificatorSql(Authentificator):
    def __init__(self):
        pass

    # аутентифицирует по бд sql
    def auth(self, username, password):
        ret = Authentificator.auth(self, username, password)
        if ret != "":
            return ret
        cur = None
        con = None
        try:
            con = sqlite3.connect(config.get("sql_auth", "users"))
            con.text_factory = str
            cur = con.cursor()
            cur.execute("""select username, password
                        from users where username=(?)""", (username, ))
            result = cur.fetchone()
            # если пользователь найден, то сравниваем хэш
            # переданного пароля с хэшем пароля, хранящимся в бд
            if result:
                if (result[1] == crypt(password, result[1][:5])):
                    return ""
                else:
                    return "(sql_auth) Invalid password"
            else:
                return "(sql_auth) User not found"
        except(sqlite3.OperationalError) as e:
            error("(sql_auth)", str(e))
            return str(e)
        finally:
            if cur is not None:
                cur.close()
            if con is not None:
                con.close()
        return ""


class AuthentificatorLdap(Authentificator):
    def __init__(self):
        pass

    def auth(self, username, password):
        ret = Authentificator.auth(self, username, password)
        if ret:
            return ret
    # аутентифицирует пользователя через ldap-сервер
        try:
            l = ldap.open(config.get("ldap", "server"))
            login_dn = config.get("ldap", "login_dn") % username
            login_pass = password
            l.simple_bind_s(login_dn, login_pass)
        except(ldap.INVALID_CREDENTIALS):
            return "INVALID LOGIN/PASSWORD"
        except(ldap.SERVER_DOWN):
            return "Server is down"
        except:
            return "Unknown error"

        return ""


class Baseinfo:
    def __init__(self, filename, timeout=10):
        self.con = sqlite3.connect(filename, timeout)
        self.con.text_factory = str
        self.cur = self.con.cursor()

    def __del__(self):
        self.cur.close()
        self.con.close()

    # записывает сессию в бд
    def write_auth_info(self, ip, username):
        end_time = None
        end_time_dt = None
        start_time = int(time.time())
        date_now = datetime.datetime.now()
        # Берем текущее время. Если час меньше 19,
        # то время конца сессии будет в 19:00 этого же дня.
        if date_now.hour < 19:
            end_time_dt = date_now.replace(hour=19, minute=0, second=0)
        else:
            # иначе, прибавляем к нему 12 часов, т.е. время конца сессии
            # будет в 7:00 следующего дня.
            end_time_dt = date_now.replace(hour=19, minute=0, second=0) + datetime.timedelta(hours=12)
        end_time = time.mktime(end_time_dt.timetuple())

        self.cur.execute("select * from addresses where ip=(?)", (ip, ))
        result = self.cur.fetchone()
        if result:
            # если пользователь логинится заново, то продляем сессию согласно логике выше
            self.cur.execute("UPDATE addresses SET `end_time`=(?),`user`=(?) WHERE `ip`=(?)", (int(end_time), username, ip))
        else:
            # а если нет, то записываем сессию
            self.cur.execute("""INSERT INTO addresses (`ip`, `user`, `start_time`, `end_time` )
            VALUES (?, ?, ?, ?)""", (ip, username, start_time, int(end_time)))
            self.cur.execute("INSERT INTO log (`ip`, `user`, `start_time` ) VALUES (\"%s\", \"%s\", \"%s\")" % (ip, username, start_time))
        self.con.commit()

    # если пользователь залогинен, и вызывает данный скрипт, то выдаем ему табличку с информацией, а также с кнопочкой "Выйти"
    def get_logged(self, ip):
        self.cur.execute("select * from addresses where ip=(?)", (ip, ))
        result = self.cur.fetchone()

        if result:
            s = template("logged", {
                "address": result[0],
                "name": result[1],
                "itime": time.asctime(time.localtime(result[2])),
                "otime": time.asctime(time.localtime(result[3]))
                })
            return s
        return ""

    def del_auth(self, ip):
        self.cur.execute("delete from addresses where ip=(?)", (ip, ))
        self.con.commit()


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])

    try:
        # парсим POST
        if ispy3():
            post = env['wsgi.input'].read().decode(encoding)
        else:
            post = env['wsgi.input'].read()
        d = parse_qs(post)
    except KeyError:
        # а если он пустой, то GET
        d = parse_qs(env['QUERY_STRING'])

    ip = env["REMOTE_ADDR"]
    username = d.get('username', [''])[0]
    password = d.get('password', [''])[0]
    url = d.get('url', ['http://google.com'])[0]
    signout = d.get('signout', [''])[0]

    username = username.lower()

    b = Baseinfo(config.get("sql", "session_db"))
    if (signout == "true"):
        b.del_auth(ip)

    logged = b.get_logged(ip)
    resp = list()
    resp.append(template("head1"))
    if (logged):
        resp.append(template("head2"))
        resp.append(logged)
        resp.append(template("signout"))
    else:
        a = AuthentificatorSql()
        auth = a.auth(username, password)
        if (auth == ""):
            resp.append("<META HTTP-EQUIV=\"refresh\" CONTENT=\"3;URL=%s\">" % url)
            resp.append(template("head2"))
            b.write_auth_info(ip, username)
            resp.append("<h1>Перенаправляю на адрес...<br></h1> <p><a href=\"%s\">%s</a></p>" % (url, url))
        else:
            resp.append("<h1 align=\"center\">Введите логин и пароль!</h1><p align=\"center\"><a href=\"%s\">%s</a></p>" % (url, url))
            resp.append(template("authform", {"url": url, "username": username, "password": password}))
            resp.append("<p align=\"center\">Error: %s</p>" % auth)

    resp.append(template("tail"))
    ret = "\n".join(resp)

    if ispy3():  # Python 3
        return ret.encode(encoding)
    else:
        return ret


def my_response(st, txt):
    print(st, txt)

if __name__ == "__main__":
    u = quote("http://google.com")
    print(application({"QUERY_STRING": "username=вася2&password=тест&url=%s" % u, "REMOTE_ADDR": "192.168.0.109"}, my_response))
