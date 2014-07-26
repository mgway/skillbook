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
        r = query_one(c, 'SELECT username FROM skillbook_user WHERE username = %s LIMIT 1', (username,))
    return r is None


def check_login(username, password):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT user_id, password, salt FROM user WHERE username = %s', (username,))
    if r is None:
        return
    salt = binascii.unhexlify(bytes(r.salt))
    h = hmac.new(salt, password.encode('utf-8'), hashlib.sha256)
    if h.hexdigest() == r.password:
        return r.id


def change_password(userid, password, new_password):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT password, salt FROM skillbook_user WHERE user_id = %s', (userid,))
        salt = binascii.unhexlify(bytes(r.salt))
        h = hmac.new(salt, password.encode('utf-8'), hashlib.sha256)
        if h.hexdigest() == r.password:
            hashed, newsalt = __hash(new_password)
            c.execute('UPDATE skillbook_user SET (password, salt) = \
                (%s, %s) WHERE user_id = %s', (hashed, newsalt, userid))
            conn.commit()
        else:
            raise UserError("Incorrect current password")


def change_preferences(userid, mail, newsletter):
    with _cursor(conn) as c:
        c.execute('UPDATE skillbook_user SET email = %s, newsletter = %s WHERE user_id = %s', 
                (mail, newsletter, userid))
        conn.commit()


def get_preferences(userid):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT email, valid_email, newsletter FROM skillbook_user WHERE user_id = %s', 
                (userid,))
        return r


def create_account(username, password):
    hashed, salt = __hash(password)
    with _cursor(conn) as c:
        c.execute('INSERT INTO skillbook_user (user_id, username, password, salt, created) \
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
                c.execute('INSERT INTO eve_character (character_id, name) VALUES (%s, %s)', 
                    (char.characterid, char.charactername))
            except psycopg2.IntegrityError:
                conn.rollback()
            # But want to disallow users from adding the same key twice
            try:
                c.execute('INSERT INTO api_key (user_id, key_id, vcode, mask, character_id) VALUES \
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
                    c.execute('INSERT INTO character_api_status (key_id, character_id, api_method, is_ignored) \
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
        c.execute('DELETE FROM api_key WHERE user_id = %s AND key_id = %s', (user, key_id))
        conn.commit()


def get_users():
    with _cursor(conn) as c:
        r = query(c, 'SELECT user_id FROM skillbook_user', [])
        return list(r)


def get_characters(user_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT name, char.character_id, key_id, vcode, mask FROM api_key keys \
            INNER JOIN eve_character char ON char.character_id = keys.character_id \
            WHERE user_id = %s', (user_id,))
        return list(r)


def get_character_briefs(user_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT name, char.character_id, char.corporation_name, balance, training_end, training_flag FROM api_key keys \
                INNER JOIN eve_character char ON char.character_id = keys.character_id WHERE user_id = %s ORDER BY name', (user_id,))
        return list(r)


def get_keys(user_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT array_agg(char.character_id) as ids, array_agg(char.name) as names, key_id, mask \
                FROM api_key keys INNER JOIN eve_character char ON char.character_id = keys.character_id \
                WHERE user_id = %s GROUP BY key_id, mask', (user_id,))
        return list(r)


def get_character(user_id, character_id):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT character_id, key_id, vcode, mask FROM api_key WHERE user_id = %s \
                AND character_id = %s', (user_id, character_id))
        return r


def get_key(user_id, key_id):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT vcode, mask from api_key WHERE user_id = %s AND key_id = %s', (user_id, key_id))
        if r:
            return key_id, r.vcode, r.key_mask


def save_character_info(character):
    with _cursor(conn) as c:
        c.execute('UPDATE eve_character SET (corporation_id, corporation_name, \
                    alliance_id, alliance_name, security) = \
                    (%(corporationid)s, %(corporation)s, %(allianceid)s, \
                    %(alliance)s, %(securitystatus)s)\
                    where character_id = %(characterid)s', character.__dict__)
        conn.commit()
        

def save_character_sheet(character):
    with _cursor(conn) as c:
        c.execute('UPDATE eve_character SET (corporation_id, corporation_name, bio, birthday, \
                    clone_grade, clone_skillpoints, balance, intelligence_base, memory_base, willpower_base, \
                    perception_base, charisma_base, intelligence_bonus, memory_bonus, willpower_bonus, \
                    perception_bonus, charisma_bonus) = \
                    (%(corporationid)s, %(corporationname)s, %(bio)s, %(birthday)s, \
                    %(clonename)s, %(cloneskillpoints)s, %(balance)s, %(intelligence)s, %(memory)s, \
                    %(willpower)s, %(perception)s, %(charisma)s, %(intelligencebonus)s, %(memorybonus)s, \
                    %(willpowerbonus)s, %(perceptionbonus)s, %(charismabonus)s) WHERE \
                    character_id = %(characterid)s', character.__dict__)
        conn.commit()
        
        current_skills = query(c, 'SELECT type_id, level, skillpoints FROM character_skill WHERE character_id = %s', 
                (character.characterid,))

        # Transform skills into a dict instead of a list
        skills = defaultdict()
        for skill in character.skills.rows:
            skills[skill.typeid] = {'level': skill.level, 'skillpoints': skill.skillpoints, 
                    'type_id': skill.typeid, 'character_id': character.characterid}

        # We need a new cursor because adding updates to cursor c's transaction during iteration 
        # breaks its internal state
        with _cursor(conn) as u:
            # Go through skills that are in the db
            for skill in current_skills:
                # We want a string key, not int
                typeid = str(skill.type_id)
                if skill.skillpoints != int(skills[typeid]['skillpoints']):
                    # Skill was trained, update it
                    u.execute('UPDATE character_skill SET (level, skillpoints, updated) = \
                            (%(level)s, %(skillpoints)s, CURRENT_TIMESTAMP) \
                            WHERE character_id = %(character_id)s AND type_id = %(type_id)s', skills[typeid])
                # Remove the skill from our list since we've handled the update
                del(skills[typeid])

            # Our set of skills from the api now contains only skills that are new
            for skill in skills.values():
                u.execute('INSERT INTO character_skill (character_id, type_id, level, skillpoints, updated) VALUES \
                        (%(character_id)s, %(type_id)s, %(level)s, %(skillpoints)s, CURRENT_TIMESTAMP)', skill)

            conn.commit()


def get_character_sheet(character_id):
    with _cursor(conn) as c:
        r = query_one(c, 'SELECT c.*, sum(cs.skillpoints) skillpoints FROM eve_character c \
            INNER JOIN character_skill cs ON cs.character_id = c.character_id \
            WHERE c.character_id = %s GROUP BY c.character_id', (character_id,)) 
        return r


def get_character_skills(character_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT s.type_id, cs.level, cs.skillpoints, \
                s.name, g.name group_name, s.description, s.primary_attribute, \
                s.secondary_attribute, s.rank, \
                c.willpower, c.perception, c.memory, c.intelligence, c.charisma\
                FROM character_skill cs INNER JOIN skill s ON s.type_id = cs.type_id \
                INNER JOIN inventory_group g on g.group_id = s.group_id \
                INNER JOIN eve_character c on c.character_id = cs.character_id\
                WHERE c.character_id = %s', (character_id,)) 
        return list(r)


def save_skill_queue(character_id, queue):
    with _cursor(conn) as c:
        # Remove current training information
        c.execute('DELETE from character_queue WHERE character_id = %s', (character_id,))

        for skill in queue.rows:
            data = skill.__dict__
            data['character_id'] = character_id
            # Bail if we don't have a start time, probably means the queue is paused
            if data['starttime'] == '':
                break
            c.execute('INSERT INTO character_queue (character_id, type_id, start_time, end_time, \
                    queue_position, level, start_skillpoints, end_skillpoints) VALUES (%(character_id)s, %(typeid)s, %(starttime)s, \
                    %(endtime)s, %(queueposition)s, %(level)s, %(startsp)s, %(endsp)s)', data)
        if queue.rows:
            # Alert the user that the queue is paused
            if queue.rows[-1].endtime == '':
                c.execute('UPDATE eve_character SET training_flag = %s WHERE character_id = %s', 
                    ('QUEUE PAUSED', character_id,))
            else:
                c.execute('UPDATE eve_character SET training_end = %s, training_flag = null WHERE character_id = %s', 
                    (queue.rows[-1].endtime, character_id))
        conn.commit()


def get_skill_queue(character_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT cq.type_id, level, start_time, end_time, queue_position, start_skillpoints, end_skillpoints, \
                s.name, c.willpower, c.perception, c.memory, c.intelligence, c.charisma, \
                s.primary_attribute, s.secondary_attribute \
                FROM character_queue cq INNER JOIN skill s ON s.type_id = cq.type_id \
                INNER JOIN eve_character c on c.character_id = cq.character_id\
                WHERE c.character_id = %s ORDER BY queue_position', (character_id,))
        return list(r)


# Get all updates for one particular key. Used for pulling in character information for a newly added key
def get_update_for_key(key_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT cas.character_id, cas.api_method, k.vcode, k.key_id, k.mask, cas.response_code \
                FROM character_api_status cas INNER JOIN api_key k on k.character_id = cas.character_id \
                AND k.key_id = cas.key_id WHERE (cas.cached_until < CURRENT_TIMESTAMP OR cas.cached_until IS NULL) \
                AND NOT is_ignored AND k.key_id = %s', (key_id,))
        return list(r)


# Get a list of all api methods to call for all characters at this time
def get_update_list():
    with _cursor(conn) as c:
        r = query(c, 'SELECT cas.character_id, cas.api_method, k.vcode, k.key_id, k.mask, cas.response_code \
                FROM character_api_status cas INNER JOIN api_key k on k.character_id = cas.character_id \
                AND k.key_id = cas.key_id WHERE (cas.cached_until < CURRENT_TIMESTAMP OR cas.cached_until IS NULL) \
                AND NOT is_ignored', ())
        return list(r)


# Now that we've performed all the API calls specified by get_update_list, 
# save the metadata about the calls
def save_update_list(updates):
    with _cursor(conn) as c:
        c.executemany('UPDATE character_api_status SET (cached_until, response_code, is_ignored) = \
                (%(cached_until)s, %(response_code)s, %(ignored)s) WHERE \
                character_id = %(character_id)s AND key_id = %(key_id)s AND api_method = %(api_method)s', updates)
        conn.commit()


# -- Static data
def get_skills():
    with _cursor(conn) as c:
        r = query(c, 'SELECT type_id, skill.group_id, group.name group_name, description, skill.name, \
                baseprice, rank, primary_attribute, secondary_attribute FROM skill \
                INNER JOIN inventory_group group ON skill.group_id = group.group_id', (None,))
        return list(r)


def get_api_calls(required_only=False):
    with _cursor(conn) as c:
        sql = 'SELECT * FROM api_call'
        if required_only:
            sql += ' WHERE is_required = TRUE'
        r = query(c, sql, ())
        return list(r)


# -- Plans
def create_plan(user_id, character_id, name, description):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plan (plan_id, user_id, character_id, name, description, created) \
                VALUES (DEFAULT, %s, %s, %s, %s, CURRENT_TIMESTAMP)',
                (user_id, character_id, name, description))
        r = query_one(c, "SELECT CURRVAL('plan_planid_seq')", None)
        conn.commit()
    return r.currval


def get_plans(user_id, character_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT plan_id, name, description FROM plans WHERE user_id = %s AND character_id = %s', 
                (user_id, character_id))
        return list(r)


def insert_plan_entries(plan_id, items):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plan_entry (plan_id, type_id, level, sprequired, priority, sort) \
                VALUES (%(planid)s, %(typeid)s, %(level)s, %(sprequired)s, %(priority)s, %(sort)s)',
                items)
        conn.commit()


def insert_plan_entry(plan_id, type_id, level, sprequired, priority, sort, meta=None):
    with _cursor(conn) as c:
        c.execute('INSERT INTO plan_entry (plan_id, type_id, level, sprequired, priority, sort) \
                VALUES (%s, %s, %s, %s, %s, %s)', (plan_id, type_id, level, sprequired, priority, sort))
        conn.commit()


def get_plan_entries(plan_id):
    with _cursor(conn) as c:
        r = query(c, 'SELECT * FROM plan_entry WHERE plan_id = %s', (plan_id,))
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
