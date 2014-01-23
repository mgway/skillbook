import binascii
import hashlib
import hmac
import io
import json
import psycopg2
import os
from collections import defaultdict

conn = psycopg2.connect("host='localhost' dbname='eveskill' user='eveskill' password='eveskill'")

def query(cursor, sql, args):
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
        c.execute('INSERT INTO users (id, username, password, salt, created) VALUES (DEFAULT, %s, %s, %s, CURRENT_TIMESTAMP)', 
                (username, hashed, salt))
        conn.commit()


def add_key(user, key_id, key_code, key_mask, characters):
    with _cursor(conn) as c:

        # Add all characters in this key
        for char in characters:
            c.execute('INSERT INTO characters (characterid, name) VALUES (%s, %s)', 
                (char.characterid, char.charactername))
            c.execute('INSERT INTO keys (userid, keyid, vcode, keymask, characterid) VALUES \
                    (%s, %s, %s, %s, %s)', (user, key_id, key_code, key_mask, char.characterid))
        conn.commit()


def remove_key(user, key_id):
    with _cursor(conn) as c:
        c.execute('DELETE FROM keys WHERE userid = %s AND keyid = %s', (user, key_id))
        conn.commit()


def get_characters_for_user(user):
    with _cursor(conn) as c:
        r = query(c, 'SELECT name, char.characterid, keyid, vcode, keymask FROM keys INNER JOIN characters char \
                ON char.characterid = keys.characterid WHERE userid = %s', (user,))
        return list(r)


def get_key(user, key_id):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT vcode, keymask from keys WHERE userid = %s AND keyid = %s', (user, key_id))
        if r:
            return key_id, r.vcode, r.keymask


def save_character_sheet(char):
    with _cursor(conn) as c:

        c.execute('UPDATE characters SET (name, corporationid, corporationname, bio, birthday, \
                    clonegrade, clonesp, balance, intelligence, memory, willpower, \
                    perception, charisma, intelligencebonus, memorybonus, willpowerbonus, \
                    perceptionbonus, charismabonus) \
                    = (%(name)s, %(corporationid)s, %(corporationname)s, %(bio)s, %(birthday)s, \
                    %(clonename)s, %(cloneskillpoints)s, %(balance)s, %(intelligence)s,\
                    %(memory)s, %(willpower)s, %(perception)s, %(charisma)s, %(intelligencebonus)s, \
                    %(memorybonus)s, %(willpowerbonus)s, %(perceptionbonus)s,%(charismabonus)s) WHERE \
                    characterid = %(characterid)s', char.__dict__)
        conn.commit()

        
        q = query(c, 'SELECT typeid, level, skillpoints FROM character_skills where characterid = %s', 
                (char.characterid,))

        # Transform skills into a dict instead of a list
        skills = defaultdict()
        for skill in char.skills.rows:
            skills[skill.typeid] = {'level': skill.level, 'skillpoints': skill.skillpoints, 
                    'typeid': skill.typeid, 'characterid': char.characterid}

        # Go through skills that are in the db
        for skill in q:
            if skill.skillpoints == skills[skill.typeid]['skillpoints']:
                # Delete items that are unchanged
                del(skills[skill.typeid])
            else:
                # Skill was trained, update it
                c.execute('UPDATE character_skills SET (characterid, typeid, level, skillpoints) = \
                        (%(characterid)s, %(typeid)s, %(level)s, %(skillpoints)s)', skills[skill.typeid])
                del(skills[skill.typeid])

        # Our set of skills from the api now contains only skills that are new
        for skill in skills.values():
            print(skill)
            c.execute('INSERT INTO character_skills (characterid, typeid, level, skillpoints) VALUES \
                    (%(characterid)s, %(typeid)s, %(level)s, %(skillpoints)s)', skill)

        conn.commit()


def save_skill_queue(characterid, queue):
    with _cursor(conn) as c:
        # Remove current training information
        c.execute('UPDATE character_skills SET (training, starttime, endtime, queueposition) = (null, null, null, null) \
                WHERE characterid = %s AND training', (characterid,))
        for skill in queue.rows:
            data = skill.__dict__
            data['characterid'] = characterid
            c.execute('UPDATE character_skills SET (training, starttime, endtime, queueposition) = \
                    (TRUE, %(starttime)s, %(endtime)s, %(queueposition)s) WHERE characterid = %(characterid)s AND typeid = %(typeid)s',
                    data)
        conn.commit()



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
