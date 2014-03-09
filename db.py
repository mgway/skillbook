import binascii
import hashlib
import hmac
import io
import json
import psycopg2
import os
from collections import defaultdict

import config

conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % \
    (config.db.host, config.db.database, config.db.user, config.db.password)

conn = psycopg2.connect(conn_string)


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


def username_available(username):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT username FROM users WHERE username = %s LIMIT 1', (username,))
    return r is None


def check_login(username, password):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT id, password, salt FROM users WHERE username = %s', (username,))
    if r is None:
        return
    salt = binascii.unhexlify(bytes(r.salt))
    h = hmac.new(salt, password.encode('utf-8'), hashlib.sha256)
    if h.hexdigest() == r.password:
        return r.id


def change_password(userid, password, new_password):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT password, salt FROM users WHERE id = %s', (userid,))
        salt = binascii.unhexlify(bytes(r.salt))
        h = hmac.new(salt, password.encode('utf-8'), hashlib.sha256)
        if h.hexdigest() == r.password:
            hashed, newsalt = __hash(new_password)
            c.execute('UPDATE users SET (password, salt) = \
                (%s, %s) WHERE id = %s', (hashed, newsalt, userid))
            conn.commit()
        else:
            raise UserError("Incorrect current password")


def change_preferences(userid, mail, newsletter):
    with _cursor(conn) as c:
        c.execute('UPDATE users SET email = %s, newsletter = %s WHERE id = %s', 
                (mail, newsletter, userid))
        conn.commit()


def get_preferences(userid):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT email, valid_email, newsletter FROM users WHERE id = %s', 
                (userid,))
        return r


def create_account(username, password):
    hashed, salt = __hash(password)
    with _cursor(conn) as c:
        c.execute('INSERT INTO users (id, username, password, salt, created) \
                VALUES (DEFAULT, %s, %s, %s, CURRENT_TIMESTAMP)', (username, hashed, salt))
        r = query_one(c, "SELECT CURRVAL('users_id_seq')", None)
        conn.commit()
    return r.currval


def add_key(user, key_id, key_code, key_mask, characters):
    with _cursor(conn) as c:
        # Add all characters in this key
        for char in characters:
            # Why two try blocks? Well, we can handle multiple characters on different keys
            try:
                c.execute('INSERT INTO characters (characterid, name) VALUES (%s, %s)', 
                    (char.characterid, char.charactername))
            except psycopg2.IntegrityError:
                conn.rollback()
            # But want to disallow users from adding the same key twice
            try:
                c.execute('INSERT INTO keys (userid, keyid, vcode, keymask, characterid) VALUES \
                        (%s, %s, %s, %s, %s)', (user, key_id, key_code, key_mask, char.characterid))
            except psycopg2.IntegrityError:
                conn.rollback()
                raise UserError('This key has already been added to your account')
            conn.commit()


def add_grants(key_id, grants, characters):
    with _cursor(conn) as c:
        for char in characters:
            for grant in grants:
                try:
                    c.execute('INSERT INTO character_api_status (keyid, characterid, method, ignored) \
                        VALUES (%s, %s, %s, %s)',
                        (key_id, char.characterid, grant['name'], grant['ignored']))
                except psycopg2.IntegrityError:
                    # Happens if the grant/keyid/characterid combination is a duplicate. In this case,
                    # someone else must have added this key to their account. No matter, since we're updating
                    # by characterid, not by userid.
                    conn.rollback()
            conn.commit()


def remove_key(user, key_id):
    with _cursor(conn) as c:
        c.execute('DELETE FROM keys WHERE userid = %s AND keyid = %s', (user, key_id))
        conn.commit()


def get_users():
    with _cursor(conn) as c:
        r = query(c, 'SELECT id FROM users', [])
        return list(r)


def get_characters(user):
    with _cursor(conn) as c:
        r = query(c, 'SELECT name, char.characterid, keyid, vcode, keymask, cached_until FROM keys \
            INNER JOIN characters char ON char.characterid = keys.characterid WHERE userid = %s', (user,))
        return list(r)


def get_character_briefs(user):
    with _cursor(conn) as c:
        r = query(c, 'SELECT name, char.characterid, char.corporationname, balance, training_end, training_flag FROM keys \
                INNER JOIN characters char ON char.characterid = keys.characterid WHERE userid = %s ORDER BY name', (user,))
        return list(r)


def get_keys(user):
    with _cursor(conn) as c:
        r = query(c, 'SELECT array_agg(char.characterid) as ids, array_agg(char.name) as names, keyid, keymask \
                FROM keys INNER JOIN characters char ON char.characterid = keys.characterid \
                WHERE userid = %s GROUP BY keyid, keymask', (user,))
        return list(r)


def get_character(user, characterid):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT characterid, keyid, vcode, keymask FROM keys WHERE userid = %s \
                AND characterid = %s', (user, characterid))
        return r


def get_key(user, keyid):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT vcode, keymask from keys WHERE userid = %s AND keyid = %s', (user, keyid))
        if r:
            return keyid, r.vcode, r.keymask


def save_character_sheet(character):
    with _cursor(conn) as c:
        c.execute('UPDATE characters SET (updated, corporationid, corporationname, bio, birthday, \
                    clonegrade, clonesp, balance, intelligence, memory, willpower, \
                    perception, charisma, intelligencebonus, memorybonus, willpowerbonus, \
                    perceptionbonus, charismabonus, cached_until) = \
                    (CURRENT_TIMESTAMP, %(corporationid)s, %(corporationname)s, %(bio)s, %(birthday)s, \
                    %(clonename)s, %(cloneskillpoints)s, %(balance)s, %(intelligence)s, %(memory)s, \
                    %(willpower)s, %(perception)s, %(charisma)s, %(intelligencebonus)s, %(memorybonus)s, \
                    %(willpowerbonus)s, %(perceptionbonus)s, %(charismabonus)s, %(cached_until)s) WHERE \
                    characterid = %(characterid)s', character.__dict__)
        conn.commit()
        
        q = query(c, 'SELECT typeid, level, skillpoints FROM character_skills WHERE characterid = %s', 
                (character.characterid,))

        # Transform skills into a dict instead of a list
        skills = defaultdict()
        for skill in character.skills.rows:
            skills[skill.typeid] = {'level': skill.level, 'skillpoints': skill.skillpoints, 
                    'typeid': skill.typeid, 'characterid': character.characterid}

        # We need a new cursor because adding updates to cursor c's transaction during iteration 
        # breaks its internal state
        with _cursor(conn) as u:
            # Go through skills that are in the db
            for skill in q:
                # We want a string key, not int
                typeid = str(skill.typeid)
                if skill.skillpoints != int(skills[typeid]['skillpoints']):
                    # Skill was trained, update it
                    u.execute('UPDATE character_skills SET (level, skillpoints, updated) = \
                            (%(level)s, %(skillpoints)s, CURRENT_TIMESTAMP) \
                            WHERE characterid = %(characterid)s AND typeid = %(typeid)s', skills[typeid])
                # Remove the skill from our list since we've handled the update
                del(skills[typeid])

            # Our set of skills from the api now contains only skills that are new
            for skill in skills.values():
                u.execute('INSERT INTO character_skills (characterid, typeid, level, skillpoints, updated) VALUES \
                        (%(characterid)s, %(typeid)s, %(level)s, %(skillpoints)s, CURRENT_TIMESTAMP)', skill)

            conn.commit()


def get_character_sheet(characterid):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT * FROM characters WHERE characterid = %s', (characterid,)) 
        return r


def get_character_skills(characterid):
    with _cursor(conn) as c:
        r = query(c, 'SELECT typeid, level, skillpoints, training, updated FROM character_skills \
                WHERE characterid = %s', (characterid,)) 
        return list(r)


def save_skill_queue(characterid, queue):
    with _cursor(conn) as c:
        # Remove current training information
        c.execute('DELETE from character_queue WHERE characterid = %s', (characterid,))

        for skill in queue.rows:
            data = skill.__dict__
            data['characterid'] = characterid
            # Bail if we don't have a start time, probably means the queue is paused
            if data['starttime'] == '':
                break
            c.execute('INSERT INTO character_queue (characterid, typeid, starttime, endtime, \
                    position, level, startsp, endsp, updated) VALUES (%(characterid)s, %(typeid)s, %(starttime)s, \
                    %(endtime)s, %(queueposition)s, %(level)s, %(startsp)s, %(endsp)s, CURRENT_TIMESTAMP)', data)
        if queue.rows:
            # Alert the user that the queue is paused
            if queue.rows[-1].endtime == '':
                c.execute('UPDATE characters SET training_flag = %s WHERE characterid = %s', 
                    ('QUEUE PAUSED', characterid,))
            else:
                c.execute('UPDATE characters SET training_end = %s, training_flag = null WHERE characterid = %s', 
                    (queue.rows[-1].endtime, characterid))
        conn.commit()


def get_skill_queue(character_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT typeid, level, starttime, endtime, position, startsp, endsp, updated \
                FROM character_queue WHERE characterid = %s ORDER BY position', (character_id,))
        return list(r)


# Get all updates for one particular key. Used for pulling in character information for a newly added key
def get_update_for_key(key_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT cas.characterid, cas.method, k.vcode, k.keyid, k.keymask, cas.response_code \
                FROM character_api_status cas INNER JOIN keys k on k.characterid = cas.characterid \
                AND k.keyid = cas.keyid WHERE (cas.cached_until < CURRENT_TIMESTAMP OR cas.cached_until IS NULL) \
                AND NOT ignored AND k.keyid = %s', (key_id,))
        return list(r)


# Get a list of all api methods to call for all characters at this time
def get_update_list():
    with _cursor(conn) as c:
        r = query(c, 'SELECT cas.characterid, cas.method, k.vcode, k.keyid, k.keymask, cas.response_code \
                FROM character_api_status cas INNER JOIN keys k on k.characterid = cas.characterid \
                AND k.keyid = cas.keyid WHERE (cas.cached_until < CURRENT_TIMESTAMP OR cas.cached_until IS NULL) \
                AND NOT ignored', ())
        return list(r)


# Now that we've performed all the API calls specified by get_update_list, 
# save the metadata about the calls
def save_update_list(updates):
    with _cursor(conn) as c:
        c.executemany('UPDATE character_api_status SET (cached_until, last_call, response_code, response_error, ignored) = \
                (%(cached_until)s, CURRENT_TIMESTAMP, %(response_code)s, %(response_error)s, %(ignored)s) WHERE \
                characterid = %(characterid)s AND keyid = %(keyid)s AND method = %(method)s', updates)
        conn.commit()


# -- Static data
def get_skills():
    with _cursor(conn) as c:
        r = query(c, 'SELECT typeid, skills.groupid, groups.name groupname, description, skills.name, \
                baseprice, timeconstant, primaryattr, secondaryattr FROM skills \
                INNER JOIN groups ON skills.groupid = groups.groupid', (None,))
        return list(r)


def get_api_calls(required_only=False):
    with _cursor(conn) as c:
        sql = 'SELECT * FROM api_calls'
        if required_only:
            sql += ' WHERE required = TRUE'
        r = query(c, sql, ())
        return list(r)


# -- Plans
def create_plan(userid, characterid, name, description):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plans (planid, userid, characterid, name, description, created) \
                VALUES (DEFAULT, %s, %s, %s, %s, CURRENT_TIMESTAMP)',
                (userid, characterid, name, description))
        r = query_one(c, "SELECT CURRVAL('plans_planid_seq')", None)
        conn.commit()
    return r.currval


def get_plans(userid, characterid):
    with _cursor(conn) as c:
        r = query(c, 'SELECT planid, name, description FROM plans WHERE userid = %s AND characterid = %s', 
                (userid, characterid))
        return list(r)


def insert_plan_entries(planid, items):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plan_entries (planid, typeid, level, sprequired, priority, sort) \
                VALUES (%(planid)s, %(typeid)s, %(level)s, %(sprequired)s, %(priority)s, %(sort)s)',
                items)
        conn.commit()


def insert_plan_entry(planid, typeid, level, sprequired, priority, sort, meta=None):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plan_entries (planid, typeid, level, sprequired, priority, sort) \
                VALUES (%s, %s, %s, %s, %s, %s)', (planid, typeid, level, sprequired, priority, sort))
        conn.commit()


def get_plan_entries(planid):
    with _cursor(conn) as c:
        r = query(c, 'SELECT * FROM plan_entries WHERE planid = %s', (planid,))
        return list(r)


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
