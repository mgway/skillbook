import binascii
import hashlib
import hmac
import io
import json
import psycopg2
import os


conn = psycopg2.connect("host='localhost' dbname='eveskill' user='eveskill' password='eveskill'")

def query(cursor, sql, *args):
    cursor.execute(sql, args)
    while True:
        r = cursor.fetchone()
        if r is None:
            break
        yield Row(r)


def _cursor(connection):
    from psycopg2.extras import RealDictCursor
    return connection.cursor(cursor_factory=RealDictCursor)


def query_one(cursor, sql, *args):
    results = query(cursor, sql, *args)
    try:
         r = next(results)
    except StopIteration:
         return
    try:
         next(results)
    except StopIteration:
         return r
    else:
         raise RuntimeError('Expected one row, got many {}, {}'.format(sql, args))


def __hash(password):
    salt = os.urandom(16)
    hashed = hmac.new(salt, password.encode('utf-8'), hashlib.sha256).hexdigest()
    return hashed, binascii.hexlify(salt)


def check_login(username, password):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT id, password, salt FROM users WHERE username = %s', (username,))
    if r is None:
        return
    salt = binascii.unhexlify(bytes(r.salt))
    h = hmac.new(salt, password.encode('utf-8'), hashlib.sha256)
    if h.hexdigest() == r.password:
        return r.id


def create_account(username, password):
    hashed, salt = __hash(password)
    with _cursor(conn) as c:
        c.execute('INSERT INTO users (id, username, password, salt, created) VALUES (DEFAULT, %s, %s, %s, CURRENT_TIMESTAMP)', (username, hashed, salt))
        conn.commit()


def add_api(user, key_id, key_code):
    #TODO see if this key actually works
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT characterid, keymask FROM characters WHERE userid = %s AND apikey = %s', 
                        (userid, key_code))


# Convenience for debugging as psycopg2 likes putting the transaction 
# into an undefined state on python error
def rollback():
    conn.rollback()


class UserError(Exception):
    def __init__(self, message):
            self.message = message

# Convert the database result from a dict to attributes, because r.value > r['value'] 
class Row:
    def __init__(self, result):
        for k,v in result.items():
            setattr(self, k, v)
        self.raw = result

    def __str__(self):
        return 'Row: ' + str(self.__dict__)
