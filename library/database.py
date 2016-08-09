# -*- coding: utf-8 -*-
"""
    A very simple wrapper for MySQLdb

    Methods:
        insert() - insert a row
        insertOrUpdate() - insert a row or update it if it exists
        update() - update rows
        delete() - delete rows
        query()  - run a raw sql query

    Implements the database connect support for each Model.
"""

import time

import mysql.connector
from mysql.connector import pooling
from mysql.connector import errors
from mysql.connector.cursor import MySQLCursorBufferedDict
from library.logger import log


def initialize_db(env):
    global connection_pool

    if 'connection_pool' not in globals():
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(**env)


def get_pooled_conn():
    conn = None
    count = 0

    while not conn and count < 3:
        try:
            conn = connection_pool.get_connection()
            break
        except errors.PoolError:
            time.sleep(0.1)
            count += 1

    return conn


def fetch_assoc(query=str, param=None, is_single_row=False, is_multi=False):

    try:
        conn = get_pooled_conn()
        cur = conn.cursor(cursor_class=BufferedDictCustom)
        cur.execute(query, param, multi=is_multi)

        if is_single_row is True:
            return cur.fetchone()
        else:
            return cur.fetchall()

    except mysql.connector.ProgrammingError as e:
        log.error('sql: %s' % query)
        log.error('fetch fail: %s' % str(e))
        raise
    except Exception as e:
        log.error('sql: %s' % query)
        log.error('fetch fail: %s' % str(e))
        raise
    finally:
        if conn:
            conn.close()


def execute(query=str, is_multi=False):

    try:
        conn = conn = get_pooled_conn()
        conn.autocommit = False
        cur = conn.cursor(cursor_class=BufferedDictCustom)
        cur.execute(query, multi=is_multi)
        result = {
            "insert_id": cur.lastrowid,
            "affected_count": cur.rowcount
        }
        conn.commit()
        return result

    except Exception as e:
        log.error('query: %s' % query)
        log.error('execute fail: %s' % str(e))
        raise
    finally:
        if conn:
            conn.close()


def execute_procedure(procedure_name=str, procedure_args=None):

    # transaction start
    # self.start_transaction(consistent_snapshot=True,
    # isolation_level=1,
    # readonly=access_mode)
    # self.start_transaction()

    try:
        conn = get_pooled_conn()
        conn.autocommit = False
        result = None
        cur = conn.cursor(cursor_class=BufferedDictCustom)
        cur.callproc(procedure_name, procedure_args)

        # result = list(cursor.fetchall())
        for result in cur.stored_results():
            log.debug('SP Result: %s' % result)

        conn.commit()
        return result

    except Exception as e:
        log.error('procedure fail: %s' % str(e))
        raise
    finally:
        conn.close()


def ping_all():

    conn_list = list()
    count = 0
    try:
        while True:
            try:
                conn = connection_pool.get_connection()
                conn_list.append(conn)

                sql = 'select 1'
                cur = conn.cursor(cursor_class=BufferedDictCustom)
                cur.execute(sql, False)
                count += 1
            except errors.PoolError:
                break
    finally:
        for c in conn_list:
            c.close()

    return count


class BufferedDictCustom(MySQLCursorBufferedDict):
    """
    Custom Cursor(3x6game)
    Json encoding시에 bytearry는 변환이 안됨.
    bytearry는 string처리 하도록 override처리 함.
    Buffered Cursor fetching rows as dictionaries.
    """

    def _row_to_python(self, rowdata, desc=None):
        """Convert a MySQL text result row to Python types

        Returns a dictionary.
        """
        row = self._connection.converter.row_to_python(rowdata, desc)
        result = dict()
        if row:
            data = dict(zip(self.column_names, row))
            for key, value in data.iteritems():

                if type(value) is bytearray:
                    value = value.decode('utf-8')
                result[key] = value

        else:
            result = None

        return result
