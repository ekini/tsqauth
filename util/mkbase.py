#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import argparse

def cmd_twi_login(name):
    pass

def main():
    KNOWN_ARGS = {
        'twi_login': (cmd_twi_login, ('twi_name',)),
}
    parser = argparse.ArgumentParser(prog='PROG')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(("-a", "--add"), action='store_true')
    group.add_argument(("-l", "--list"), action='store')
    opt, args = parser.parse_args()
    for action in args:
        if action not in KNOWN_ARGS:
            parser.error('Unknown action: <%s>' % action)

    config = ConfigParser.ConfigParser()
    config.read("/etc/squid-transparent-auth/config.cfg")
    print config.get("sql", "session_db")
if __name__=="__main__":
    main()
