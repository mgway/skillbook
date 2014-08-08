import redis
import pickle
import simplejson

import config

r = redis.StrictRedis(host=config.redis.host, port=config.redis.port, db=config.redis.db)

def exists(key):
    return r.exists(key)


def store(key, data, method='json', expire_at=None, expires=900):
    if method == 'json':
        to_store = _encode_json(data)
    elif method == 'pickle':
        to_store = pickle.dumps(data)
    else:
        raise NotImplementedError('The storage method %s is not implemented' % method)

    key = '%s:%s' % (method, key)
    r.set(key, to_store)

    if expires:
        r.expire(key, expires)
    if expire_at:
        r.expireat(key, calendar.timegm(expire.utctimetuple()))

    return to_store


def fetch(key, result='json'):
    # Try fetching the cached version in the format we want
    key = '%s:%s' % (result, key)
    data = r.get(key)
    
    # If it's there, great
    if data:
        return data

    # if not, see if we have it stored in another format
    keys = r.keys('*:%s' % key)
    for key in keys:
        # Pull it from redis
        method = str(key).split(':')[0]
        if method == 'json':
            data = simplejson.loads(r.get(key))
        elif method == 'pickle':
            data = pickle.loads(r.get(key))

        # Make it into the result format
        if result == 'json':
            return _encode_json(data)
        elif result == 'pickle':
            return pickle.dumps(data)
        else:
            return data # 'native'


# Remove the key
def remove(key, all_formats=True):
    multi_key = '*:' + key if all_formats else key 
    for key in r.keys(multi_key):
        r.delete(key)


# Decorator for automatically caching the result of a function. The cache key is
# of the form: 'method:key:arg_or_kwarg_value
def cached(key, arg_pos=None, kwarg_name=None, method='json', expires=900):
    def wrap(fn, *args, **kwargs):
        def wrapped_fn(*args, **kwargs):

            # Extract a unique identifier for the key out of the 
            # method invocation
            full_key = key
            if arg_pos != None:
                full_key = '%s:%s' % (key, args[arg_pos])
            elif kwarg_name != None:
                full_key = '%s:%s' % (key, kwargs[kwarg_name])

            data = fetch(full_key, result=method)
            if not data:
                result = fn(*args, **kwargs)
                data = store(full_key, result, method=method, expires=expires)
            return data
        return wrapped_fn
    return wrap

# Decorator for automatically removing a cached element. 
def bust(key, arg_pos=None, kwarg_name=None, all_formats=True):
    def wrap(fn, *args, **kwargs):
        def wrapped_fn(*args, **kwargs):

            # Extract a unique identifier for the key out of the 
            # method invocation
            full_key = key
            if arg_pos != None:
                full_key = '%s:%s' % (key, args[arg_pos])
            elif kwarg_name != None:
                full_key = '%s:%s' % (key, kwargs[kwarg_name])
            
            data = fn(*args, **kwargs)
            remove(full_key, all_formats)
            
            return data
        return wrapped_fn
    return wrap


def _encode_json(data):
    def json_handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))

    return simplejson.dumps(data, use_decimal=True, default=json_handler)
