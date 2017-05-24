# -*- coding: utf-8 -*-
"""
    A very simple wrapper for SQLite3

"""

import sqlite3

conn = sqlite3.connect('/tmp/gfun-gameserver.db')


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def initialize():

    conn.row_factory = dict_factory
    c = conn.cursor()

    # drop and Create table
    c.execute("Drop TABLE if EXISTS users")
    c.execute("CREATE TABLE users (envName text, gameRegId text, gameAccessId text, gUserKey text, gSumScore real)")

    # Insert a row of data
    # c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")

    # Save (commit) the changes
    conn.commit()

    c.fetchall()

    # We can also close the connection if we are done with it.
    #  Just be sure any changes have been committed or they will be lost.
    # conn.close()

