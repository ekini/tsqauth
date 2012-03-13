#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser

def main():
    config = ConfigParser.ConfigParser()
    config.read("/etc/squid-transparent-auth/config.cfg")
    print config.get("sql", "session_db")
if __name__=="__main__":
    main()
