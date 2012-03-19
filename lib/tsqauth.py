#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

conffile = "/etc/tsqauth/config.cfg"

def error(*e):
    l = list(e)
    l.insert(0, "Error:")
    l.append("\n")
    sys.stderr.write(" ".join(l))

if __name__=="__main__":
    pass
