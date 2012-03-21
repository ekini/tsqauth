#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
import string

try:
    import configparser  # python3
except ImportError:
    import ConfigParser as configparser  # python2

conffile = "/etc/tsqauth/config.cfg"
encoding = None

try:
    config = configparser.ConfigParser()
    config.readfp(open(conffile))
    encoding = config.get("global", "encoding")
except IOError as e:
    error(str(e))
except configparser.NoOptionError:
    encoding = "utf-8"

def error(*e):
    l = list(e)
    l.insert(0, "Error:")
    l.append("\n")
    sys.stderr.write(" ".join(l))


def ispy3():
    if sys.version_info[0] >= 3:  # Python 3
        return True
    else:  # Python 2
        return False


def getsalt(chars=string.ascii_letters + string.digits):
    # generate a random 2-character 'salt'
    return random.choice(chars) + random.choice(chars)


def template(name, args=dict()):
    c = config.get("html", name)
    template = string.Template(c)
    return template.safe_substitute(args)


def main():
    pass

if __name__ == "__main__":
    main()
