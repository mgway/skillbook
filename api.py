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
        try:
            result = row.raw
            if row.api_method == 'CharacterSheet':
                data = eveapi.character_sheet(row.key_id, row.vcode, row.mask, row.character_id)
                # Fudge the cached_until timer because it always returns ~30 seconds, and we
                # don't care to update that often
                data.cached_until = data.cached_until + datetime.timedelta(minutes=30)
                db.save_character_sheet(data)
                cache.remove("*:sheet:%s" % row.character_id)
                cache.remove("*:skills:%s" % row.character_id)
            elif row.api_method == 'SkillQueue':
                data = eveapi.skill_queue(row.key_id, row.vcode, row.mask, row.character_id)
                db.save_skill_queue(row.character_id, data.skillqueue)
                cache.remove("*:queue:%s" % row.character_id)
            else:
                raise SkillbookException('Unknown API method %s' % row.api_method)

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


def remove_key(user_id, key_id):
    db.remove_key(user_id, key_id)
    cache.remove('characters:%s' % user_id)


def add_key(user_id, key_id, vcode):
    mask, characters = eveapi.key_info(key_id, vcode)

    # Make sure the key has the minimum amount access
    requirements = db.get_api_calls()
    grants = []
    for req in requirements:
        if int(mask) & req.mask == 0:
            if req.is_required:
                raise SkillbookException('The supplied key is missing the %s permission' % req.name)
        else:
            grants.append({'name': req.name, 'ignored': not req.is_required})

    db.add_key(user_id, key_id, vcode, mask, characters.key.characters.rows)
    db.add_grants(key_id, grants, characters.key.characters.rows)
    perform_updates(key_id=key_id)
    cache.remove('*:characters:%s' % user_id)


@cached('characters', arg_pos=0, expires=30)
def get_characters(user_id):
    return [char.raw for char in db.get_character_briefs(user_id)]


@cached('sheet', arg_pos=1)
def get_character_sheet(user_id, character_id):
    if db.get_character(user_id, character_id):
        return db.get_character_sheet(character_id).raw
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('skills', arg_pos=1)
def get_character_skills(user_id, character_id):
    if db.get_character(user_id, character_id):
        skills = db.get_character_skills(character_id)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('queue', arg_pos=1)
def get_character_queue(user_id, character_id):
    if db.get_character(user_id, character_id):
        skills = db.get_skill_queue(character_id)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('static:skills')
def get_skills():
    db_skills = db.get_skills()
    skills_dict = dict()
    for skill in db_skills:
        skills_dict[skill.type_id] = skill.raw
    return skills_dict


class SkillbookException(Exception):
    def __init__(self, message):
        self.message = message
    def __repr__(self):
        return self.message
