import db
import eveapi
import cache
import tasks
from cache import cached, bust


# API key management
def get_keys(user_id):
    return db.get_keys(user_id)


@bust('characters', arg_pos=0)
def remove_key(user_id, key_id):
    db.remove_key(user_id, key_id)


@bust('characters', arg_pos=0)
def add_key(user_id, key_id, vcode):
    mask, characters, expires = eveapi.key_info(key_id, vcode)

    # Make sure the key has the minimum amount access
    requirements = db.get_api_calls()
    grants = []
    for req in requirements:
        if int(mask) & req.mask == 0 and req.mask != 0 and req.is_required:
            raise SkillbookException('The supplied key is missing the %s permission' % req.name)
        else:
            grants.append({'name': req.name, 'ignored': not req.is_required})

    db.add_key(user_id, key_id, vcode, mask, expires, characters.key.characters.rows)
    db.add_grants(key_id, grants, characters.key.characters.rows)
    tasks.perform_updates.delay(key_id=key_id)

# Character/skills
@cached('characters', arg_pos=0, expires=30)
def get_characters(user_id):
    return db.get_character_briefs(user_id)


@cached('character-sheet', arg_pos=1)
def get_character_sheet(user_id, character_id):
    if db.get_character(user_id, character_id) != None:
        return db.get_character_sheet(character_id).raw
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('character-skills', arg_pos=1)
def get_character_skills(user_id, character_id):
    if db.get_character(user_id, character_id) != None:
        return db.get_character_skills(character_id)
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('character-queue', arg_pos=1)
def get_character_queue(user_id, character_id):
    if db.get_character(user_id, character_id) != None:
        return db.get_skill_queue(character_id)
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('character-plans', arg_pos=1)
def get_character_plans(user_id, character_id):
    if db.get_character(user_id, character_id) != None:
        return db.get_plans(user_id, character_id)
    else:
        raise SkillbookException('You do not have permission to view this character')


@cached('character-alerts', arg_pos=1)
def get_character_alerts(user_id, character_id):
    if db.get_character(user_id, character_id) != None:
        mail_attributes = db.get_email_attributes(user_id)
        alerts = db.get_character_alerts(user_id, character_id)
        return {'alerts': alerts, 'unsubscribed': mail_attributes.unsubscribed, 
            'valid_email': mail_attributes.valid_email}
    else:
        raise SkillbookException('You do not have permission to view this character')


@bust('character-alerts', arg_pos=1)
def set_character_alerts(user_id, character_id, alerts):
    if db.get_character(user_id, character_id) != None:
        db.set_character_alerts(user_id, character_id, alerts)
    else:
        raise SkillbookException('You do not have permission to modify this character')


# Plans
@cached('plans', arg_pos=0)
def get_plans(user_id):
    return db.get_plans(user_id)


@bust('plans', arg_pos=0)
def add_plan(user_id, character_id, name, description):
    plan_id = db.add_plan(user_id, character_id, name, description)


@cached('plan', arg_pos=1)
def get_plan(user_id, plan_id):
    plan = db.get_plan(user_id, plan_id).raw
    plan['entries'] = db.get_plan_entries(plan_id)
    return plan


@bust('plan', arg_pos=0)
def add_plan_entry(plan_id, type_id, level, priority, sort, meta=None):
    db.add_plan_entry(plan_id, type_id, level, priority, sort, meta)


@cached('static:skills')
def get_all_skills():
    db_skills = db.get_skills()
    skills_dict = dict()
    for skill in db_skills:
        skills_dict[skill['type_id']] = skill
    return skills_dict


@cached('static:alerts')
def get_all_alerts():
    return db.get_alerts()


class SkillbookException(Exception):
    def __init__(self, message):
        self.message = message
    def __repr__(self):
        return self.message
