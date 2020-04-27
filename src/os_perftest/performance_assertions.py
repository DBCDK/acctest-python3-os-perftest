#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`os_perftest.performance_assertions` -- assert statements
==============================================================
"""

def assertZero( dump, entry, path ):
    key = path.split( '/' )[-1]
    value = dump.read_values( entry, path )[-1]
    if int( value ) != 0:
        raise Exception("%s is non-zero (%d)"%( key, value ))

def assertNotZero( dump, entry, path ):
    key = path.split( '/' )[-1]
    value = dump.read_values( entry, path )[-1]
    if int( value ) == 0:
        raise Exception("%s is zero"%key)
