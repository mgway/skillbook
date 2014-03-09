import db
import eveapi
import cache
import datetime
from cache import cached
from psycopg2.tz import FixedOffsetTimezone


def perform_updates(key_id=None):
    if key_id:
        updates = db.get_update_for_key(key_id)
    else:
        updates = db.get_update_list()
    results = []
    for row in updates:
        print(row.raw)
        try:
            result = row.raw
            if row.method == 'CharacterSheet':
                data = eveapi.character_sheet(row.keyid, row.vcode, row.keymask, row.characterid)
                # Fudge the cached_until timer because it always returns ~30 seconds, and we
                # don't care to update that often
                data.cached_until = data.cached_until + datetime.timedelta(minutes=15)
                db.save_character_sheet(data)
                print('Cached until:')
                print(data.cached_until)
            elif row.method == 'SkillQueue':
                data = eveapi.skill_queue(row.keyid, row.vcode, row.keymask, row.characterid)
                db.save_skill_queue(row.characterid, data.skillqueue)
            else:
                raise SkillbookException('Unknown API method %s' % row.method)

            # Fix the timezone, they give us UTC which might not be the TZ of the server
            result.update({'cached_until': data.cached_until.replace(tzinfo=FixedOffsetTimezone(0)), 
                'response_code': 200, 'response_error': '', 'ignored': False})
            results.append(result)
        except Exception as e:
            # Ignore this call in the future if we've gotten an error before
            ignored = True if row.response_code == 500 else False

            result.update({'cached_until': None, 'response_code': 500, 
                'response_error': repr(e), 'ignored': ignored})
            results.append(result)

    db.save_update_list(results)


def remove_key(userid, keyid):
    db.remove_key(userid, keyid)
    cache.remove('characters:%s' % userid)


def add_key(user_id, key_id, vcode):
    mask, characters = eveapi.key_info(key_id, vcode)

    # Make sure the key has the minimum amount access
    requirements = db.get_api_calls()
    grants = []
    for req in requirements:
        if req.required and int(mask) & req.mask == 0:
            raise SkillbookException('The supplied key is missing the %s permission' % req.name)
        grants.append({'name': req.name, 'ignored': not req.required})

    db.add_key(user_id, key_id, vcode, mask, characters.key.characters.rows)
    db.add_grants(key_id, grants, characters.key.characters.rows)
    perform_updates(key_id=key_id)


@cached('characters', arg_pos=0)
def get_characters(userid):
    return [char.raw for char in db.get_character_briefs(userid)]


@cached('sheet', arg_pos=1)
def get_character_sheet(userid, characterid):
    if db.get_character(userid, characterid):
        return db.get_character_sheet(characterid).raw
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('skills', arg_pos=1)
def get_character_skills(userid, characterid):
    if db.get_character(userid, characterid):
        skills = db.get_character_skills(characterid)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('queue', arg_pos=1)
def get_character_queue(userid, characterid):
    if db.get_character(userid, characterid):
        skills = db.get_skill_queue(characterid)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('static:skills')
def get_skills():
    db_skills = db.get_skills()
    skills_dict = dict()
    for skill in db_skills:
        skills_dict[skill.typeid] = skill.raw
    return skills_dict


class SkillbookException(Exception):
    def __init__(self, message):
        self.message = message
    def __repr__(self):
        return self.message
