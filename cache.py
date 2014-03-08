import redis
import pickle
import simplejson

r = redis.StrictRedis(host='localhost', port=6379, db=0)

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


def remove(key):
    r.delete(r.keys(key))


def cached(key, arg_pos=None, kwarg_name=None, method='json'):
    def wrap(fn, *args, **kwargs):
        def wrapped_fn(*args, **kwargs):

            # Extract a unique identifier for the key out of the 
            # method invocation
            full_key = key
            if arg_pos:
                full_key = '%s:%s' % (key, args[arg_pos])
            elif kwarg_name:
                full_key = '%s:%s' % (key, kwargs[kwarg_name])

            data = fetch(full_key, result=method)
            if not data:
                result = fn(*args, **kwargs)
                data = store(full_key, result, method=method)
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
