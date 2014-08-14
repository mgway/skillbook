import yaml

class Config(object):
    def __init__(self, config):
        for k, v in config[self.key].items():
            del(self.attrs[k])
            setattr(self, k, v)

class WebConfig(Config):
    key = 'web'
    attrs = dict([
        ('port', 8888),
        ('host', 'localhost'),
        ('cookie_secret', 'You should probably change this'),
        ('debug', True),
        ('https', False)
    ])

class DBConfig(Config):
    key = 'db'
    attrs = dict([
        ('host', 'localhost'),
        ('port', 5432),
        ('user', 'eveskill'),
        ('password', 'eveskill'),
        ('database', 'eveskill'),
    ])

class RedisConfig(Config):
    key = 'redis'
    attrs = dict([
        ('host', 'localhost'),
        ('port', 6379),
        ('db', 0)
    ])

class MailgunConfig(Config):
    key = 'mailgun'
    attrs = dict([
        ('key', 'key-1234567'),
        ('public_key', 'pubkey-1234567'),
        ('url', 'example.com'),
        ('from_address', 'noreply@domain.com')
    ])

class CeleryConfig(Config):
    key = 'celery'
    attrs = dict([
        ('broker_url', 'redis://localhost:6379/1'),
        ('backend_url', 'redis://localhost:6379/1')
    ])

try:
    conf = yaml.load(open('config.yaml', 'r'))
except FileNotFoundError:
    conf = dict()

web = WebConfig(conf)
db = DBConfig(conf)
redis = RedisConfig(conf)
mail = MailgunConfig(conf)
celery = CeleryConfig(conf)