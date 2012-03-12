#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
from urlparse import parse_qs
import urllib
import ldap 
import os # for os.environ
import pysqlite2
from pysqlite2 import dbapi2 as sqlite3
import time # for time.sleep and time conversion functions
import datetime 
import hashlib
import base64

# Адрес ldap сервера в случае авторизации через ldap-server или путь к файлу БД с пользователями в случае sql.
#path = "192.168.0.4"
path = "/usr/libexec/squidldapauth/users.db"
# метод аутентификации, может быть "ldap" или "sql"
method="sql"

template_head1=u"""
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
"""
template_head2=u"""
<title>Авторизация</title>
</head>
<body>"""
template_authform=u"""
<form method=post>
<table align="center" border="0">
<tr><td>
<input type="hidden" name="url" value="%s">
Логин:</td><td><input type="text" name="username" value="%s"></td>
</tr>
<tr><td>
Пароль:</td><td><input type="password" name="password" value="%s"></td>
</tr>
<tr><td>
<input type=submit>
</td></tr>
</table>
</form>
"""
template_tail=u"""</body>
</html>
"""
template_signout=u"""
<form method=post><input type="hidden" name="signout" value="true"><input type=submit value="Выйти"></form>
"""

def passwd(p):
    m = hashlib.md5()
    m.update(p)
    return base64.b64encode(m.digest())

class Authentificator:
    def __init__(self):
        if (method == "ldap"):
            self.a = self.auth_ldap
        if (method == "sql"):
            self.a = self.auth_sql
        else:
            self.a = self.auth_ldap
    # общая функция аутентификации, вызывает auth_ldap или auth_sql в зависимости от значения переменной "method"
    def auth(self, username, password):
        # если логин или пароль пустой, то выводим ошибку
        if (username == "" or password == ""): return "Enter login and password"
        ret = self.a(username, password)
        # если конкретная функция выдала строку, значит аутентификация не прошла, выводим то, что она выдала
        if (ret != ""):
            return "(%s) %s" % (method, ret)
        # а если прошла, то выводим пустую строку
        else:
            return ""
    # аутентифицирует по бд sql
    def auth_sql(self, username, password):
        try:
            con = sqlite3.connect(path)
            cur = con.cursor()
            cur.execute("select * from users where username=\'%s\';" % username)
            result = cur.fetchone()
            # если пользователь найден, то сравниваем хэш переданного пароля с хэшем пароля, хранящимся в бд
            if result:
                if (result[1] == passwd(password)):
                    return ""
                else:
                    return "Invalid password"
            else:
                return "User not found"
            cur.close()
            con.close()
        except(pysqlite2.dbapi2.OperationalError) as e:
            return e

    # аутентифицирует пользователя через ldap-сервер
    def auth_ldap(self, username, password):
        try:
            l = ldap.open(path)
            login_dn = "uid=%s,ou=internetusers,dc=vnipiomsk,dc=ru" % username
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
    def __init__(self, filename = "/usr/libexec/squidldapauth/ip.db", tries = 5): # tries - количество попыток записать что-то в базу. Интервал между ними - 1 с.
        self.tries = tries
        self.con = sqlite3.connect(filename)
        self.cur = self.con.cursor()
        # создаем таблицы. В таблице addresses хранятся текущие сессии, а в log - соответсвенно, прошлые :)
        self.cur.execute("""
        create table if not exists addresses
        (
            ip    varchar(15) NOT NULL,
            user  varchar(32) NOT NULL,
            start_time    uint(11) NOT NULL,
            end_time  uint(11) NOT NULL
        )""")
        self.cur.execute("""
        create table if not exists log 
        (
            ip    varchar(15) NOT NULL,
            user  varchar(32) NOT NULL,
            start_time    uint(11) NOT NULL
        )
        """)
        self.con.commit()

    def __del__(self):
        self.cur.close()
        self.con.close()

    # сделано на случай, если несколько процессов захотят одновременно записать что-то в бд.
    def failsafe_execute(self, query):
        for x in range(0, self.tries):
            try:
                self.cur.execute(query)
                break
            except sqlite3.OperationalError:
                time.sleep(1)
                pass

    # записывает сессию в бд
    def write_auth_info(self, ip, username):
        end_time = None
        end_time_dt = None
        start_time = int(time.time())
        date_now = datetime.datetime.now()
        # Берем текущее время. Если час меньше 19, то время конца сессии будет в 19:00 этого же дня.
        if date_now.hour < 19:
            end_time_dt = date_now.replace(hour=19,minute=0,second=0)
        else:
            # иначе, прибавляем к нему 12 часов, т.е. время конца сесси будет в 7:00 следующего дня.
            end_time_dt = date_now.replace(hour=19,minute=0,second=0)+datetime.timedelta(hours=12)
        end_time = time.mktime(end_time_dt.timetuple())

        self.failsafe_execute("select * from addresses where ip=\'%s\';" % ip)
        result = self.cur.fetchone()
        if result:
            # если пользователь логинится заново, то продляем сессию согласно логике выше
            self.failsafe_execute("UPDATE addresses SET `end_time`=\"%s\",`user`=\"%s\" WHERE `ip`=\"%s\"" % (int(end_time), username, ip))
        else:
            # а если нет, то записываем сессию 
            self.failsafe_execute("INSERT INTO addresses (`ip`, `user`, `start_time`, `end_time` ) VALUES (\"%s\", \"%s\", \"%s\", \"%s\")" % (ip, username, start_time, int(end_time)))
            self.failsafe_execute("INSERT INTO log (`ip`, `user`, `start_time` ) VALUES (\"%s\", \"%s\", \"%s\")" % (ip, username, start_time))
        self.con.commit()

    # если пользователь залогинен, и вызывает данный скрипт, то выдаем ему табличку с информацией, а также с кнопочкой "Выйти"
    def get_logged(self, ip):
        self.failsafe_execute("select * from addresses where ip=\'%s\';" % ip)
        result = self.cur.fetchone()
        if result:
            s = u"<table><tr><td>Зашел с адреса</td><td>%s</td></tr><tr><td>под именем</td><td>%s</td></td><tr><td>Время захода</td><td>%s</td></tr><tr><td>Время выхода</td><td>%s</td></table>" % (result[0], result[1], time.asctime(time.localtime(result[2])), time.asctime(time.localtime(result[3])))
            return s 
        return u""

    def del_auth(self,ip):
        self.failsafe_execute("delete from addresses where ip=\'%s\';" % ip)
        self.con.commit()

def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])

    try:
        # парсим POST
        d = parse_qs(env['wsgi.input'].read())
    except (KeyError):
        # а если он пустой, то GET
        d = parse_qs(env['QUERY_STRING'])

    ip = env["REMOTE_ADDR"]
    username = d.get('username', [''])[0]
    password = d.get('password', [''])[0]
    url      = d.get('url', ['http://google.com'])[0]
    signout  = d.get('signout', [''])[0]

    # ескейпим данные, полученные от пользователя
    username = cgi.escape(username)
    password = cgi.escape(password)
    url      = cgi.escape(url)
    signout = cgi.escape(signout)

    b = Baseinfo()
    if (signout == "true"):
        b.del_auth(ip)
    logged = b.get_logged(ip)

    resp = u""
    resp += template_head1 

    if (logged != ""):
        resp += template_head2   
        resp += logged
        resp += template_signout
    else:
        a = Authentificator()
        auth = a.auth(username, password)
        if (auth == ""):
            resp += u"<META HTTP-EQUIV=\"refresh\" CONTENT=\"3;URL=%s\">" % url 
            b.write_auth_info(ip, username)
            resp += u"<h1>Перенаправляю на адрес...<br></h1> <p><a href=\"%s\">%s</a></p>"% (url, url)
        else:
            resp += u"<h1 align=\"center\">Введите логин и пароль!</h1><p align=\"center\"><a href=\"%s\">%s</a></p>" % (url, url)
            resp += template_authform % (url, username, password)
            resp += u"<p align=\"center\">Error: %s</p>" % auth
        resp += template_head2   

    resp += template_tail

    return resp.encode("utf-8")

def my_response(st, txt):
    print st, txt

if __name__=="__main__":
    u = urllib.quote("http://google.com")
    print application({"QUERY_STRING" : "username=Dementiev&password=338857&url=%s" % u, "REMOTE_ADDR" : "192.168.0.108"}, my_response )

