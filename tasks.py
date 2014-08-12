from celery import Celery
from celery.schedules import crontab
import datetime

import config
import eveapi
import cache
import mail
import db

app = Celery('tasks',
             broker=config.celery.broker_url,
             backend=config.celery.backend_url)

schedule = {
    'perform_updates_every_15m': {
        'task': 'tasks.perform_updates',
        'schedule': crontab(minute='*/15')
    },
}
app.conf.update(CELERYBEAT_SCHEDULE = schedule)


@app.task
def perform_updates(key_id=None):
    if key_id:
        rows = db.get_update_for_key(key_id)
    else:
        rows = db.get_update_list()

    for row in rows:
        if row.api_method == 'APIKeyInfo':
            update_api_key.delay(row.key_id, row.vcode, row.character_id)
        if row.api_method == 'CharacterSheet':
            update_character_sheet.delay(row.key_id, row.vcode, row.mask, row.character_id)
        elif row.api_method == 'SkillQueue':
            update_character_queue.delay(row.key_id, row.vcode, row.mask, row.character_id)
        elif row.api_method == 'CharacterInfo':
            update_character_info_public.delay(row.key_id, row.character_id)
        else:
            raise SkillbookException('Unknown API method %s' % row.api_method)


@app.task
def update_api_key(key_id, vcode, character_id):
    mask, characters, expires = eveapi.key_info(key_id, vcode)
    # Fudge the cached_until timer
    data.cached_until = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    #db.update_api_key(key_id, vcode, mask, expires)
    
    stat = {'cached_until': data.cached_until.replace(tzinfo=FixedOffsetTimezone(0)),
            'response_code': 200,
            'response_error': '',
            'character_id': character_id,
            'api_method': 'APIKeyInfo',
            'ignored': False,
            'key_id': key_id}
    db.save_update_status(stat)
    
    # Handle key expiry alert
    alerts = db.get_alert('API_KEY', character_id)
    for alert in alerts:
        cooldown = datetime.datetime.utcnow() + datetime.timedelta(minutes=alert.interval)
        if expires - datetime.timedelta(days=int(alert.option_1_value)) < datetime.datetime.utcnow():
            mail.send_alert(alert.user_id, alert, None)
            db.update_alert(alert.alert_type_id, alert.user_id, alert.character_id, cooldown)


@app.task
def update_character_sheet(key_id, vcode, mask, character_id):
    data = eveapi.character_sheet(key_id, vcode, mask, character_id)
    # Fudge the cached_until timer because it always returns ~30 seconds, and we
    # don't care to update that often
    data.cached_until = data.cached_until + datetime.timedelta(minutes=30)
    db.save_character_sheet(data)
    cache.remove("character-sheet:%s" % character_id)
    cache.remove("character-skills:%s" % character_id)
    
    stat = {'cached_until': data.cached_until,
            'response_code': 200,
            'response_error': '',
            'character_id': character_id,
            'api_method': 'CharacterSheet',
            'ignored': False,
            'key_id': key_id}
    db.save_update_status(stat)
    
    # Handle clone status alert
    alerts = db.get_alert('CLONE_CAPACITY', character_id)
    skillpoints = sum(int(skill.skillpoints) for skill in data.skills.rows)
    
    for alert in alerts:
        cooldown = datetime.datetime.utcnow() + datetime.timedelta(minutes=alert.interval)
        remaining = int(data.cloneskillpoints) - skillpoints
        if remaining < alert.option_1_value:
            mail.send_alert(alert.user_id, alert, remaining)
            db.update_alert(alert.alert_type_id, alert.user_id, alert.character_id, cooldown)


@app.task
def update_character_queue(key_id, vcode, mask, character_id):
    data = eveapi.skill_queue(key_id, vcode, mask, character_id)
    db.save_skill_queue(character_id, data.skillqueue)
    cache.remove("character-queue:%s" % character_id)
    
    stat = {'cached_until': data.cached_until,
            'response_code': 200,
            'response_error': '',
            'character_id': character_id,
            'api_method': 'CharacterQueue',
            'ignored': False,
            'key_id': key_id}
    db.save_update_status(stat)
    
    # Handle queue length alert
    alerts = db.get_alert('QUEUE_TIME', character_id)
    for alert in alerts:
        cooldown = datetime.datetime.utcnow() + datetime.timedelta(minutes=alert.interval)
        if len(data.skillqueue.rows) == 0:
            return
        last_skill = data.skillqueue.rows[-1]
        if last_skill.endtime != '':
            end_time = datetime.datetime.strptime(last_skill.endtime, '%Y-%m-%d %H:%M:%S')
            if end_time - datetime.timedelta(hours=int(alert.option_1_value)) < datetime.datetime.utcnow():
                mail.send_alert(alert.user_id, alert, end_time)
                db.update_alert(alert.alert_type_id, alert.user_id, alert.character_id, cooldown)


@app.task
def update_character_info_public(key_id, character_id):
    data = eveapi.character_info(character_id)
    db.save_character_info(data)
    cache.remove("character-sheet:%s" % character_id)
    
    stat = {'cached_until': data.cached_until,
            'response_code': 200,
            'response_error': '',
            'character_id': character_id,
            'api_method': 'CharacterInfo',
            'ignored': False,
            'key_id': key_id}
    db.save_update_status(stat)


# Proxy for async mail sending
@app.task
def send_mail(to, subject, text=None, html=None):
    mail.send(to, subject, text=None, html=None)
