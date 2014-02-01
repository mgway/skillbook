import db
import eveapi

def update_characters_for_user(userid):
    for row in db.get_characters(userid):
        sheet = eveapi.character_sheet(row.keyid, row.vcode, row.keymask, row.characterid)
        queue = eveapi.skill_queue(row.keyid, row.vcode, row.keymask, row.characterid)
        db.save_character_sheet(sheet)
        db.save_skill_queue(row.characterid, queue.skillqueue)


def get_character_sheet(userid, characterid):
    data = db.get_character(userid, characterid)
    return db.get_character_sheet(characterid)


def get_skill_queue(userid, characterid):
    data = db.get_character(userid, characterid)
    return db.get_skill_queue(characterid)


def add_key(userid, keyid, vcode):
    mask, characters = eveapi.key_info(keyid, vcode)
    print(characters.key)
    db.add_key(userid, keyid, vcode, mask, characters.key.characters.rows)


def get_characters(userid):
    characters = db.get_character_briefs(userid)
    return [char.raw for char in characters]


def get_character_sheet(userid, characterid):
    if db.get_character(userid, characterid):
        return db.get_character_sheet(characterid).raw
    else:
        raise SkillbookException('You do not have permission to view this character')


def get_character_skills(userid, characterid):
    if db.get_character(userid, characterid):
        skills = db.get_character_skills(characterid)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


def get_character_queue(userid, characterid):
    if db.get_character(userid, characterid):
        skills = db.get_skill_queue(characterid)
        return [skill.raw for skill in skills]
    else:
        raise SkillbookException('You do not have permission to view this character')


class SkillbookException(Exception):
    def __init__(self, message):
        self.message = message
