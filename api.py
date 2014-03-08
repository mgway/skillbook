import db
import eveapi
import cache
from cache import cached
import datetime


def update_all_characters():
    users = db.get_users()
    for user in users:
        update_characters_for_user(user.id)


def update_characters_for_user(userid):
    for row in db.get_characters(userid):
        if not row.cached_until or row.cached_until < datetime.datetime.now():
            sheet = eveapi.character_sheet(row.keyid, row.vcode, row.keymask, row.characterid)
            queue = eveapi.skill_queue(row.keyid, row.vcode, row.keymask, row.characterid)
            db.save_character_sheet(sheet)
            db.save_skill_queue(row.characterid, queue.skillqueue)

            # Remove all cached items for this characterid
            cache.remove('*:%s'%row.characterid)


def add_key(userid, keyid, vcode):
    mask, characters = eveapi.key_info(keyid, vcode)

    # Make sure the key has the minimum amount access
    requirements = {'8':'CharacterSheet', '131072': 'SkillTraining', '262144':'SkillQueue', 
            '16777216':'CharacterInfo', '33554432':'AccountStatus'}
    for req in requirements.keys():
        if int(mask) & int(req) == 0:
            raise SkillbookException('The supplied key is missing the %s permission' % requirements[req])

    db.add_key(userid, keyid, vcode, mask, characters.key.characters.rows)


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
