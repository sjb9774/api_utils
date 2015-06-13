import json
app = None
validation_callback = None

def api_call(route='/',
             validation_required=True,
             required_args=None,
             validate_callback=None,
             **kwargs):
    global app
    global validation_callback
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # get arguments as passed to function or from query string
            if len(args) == 1:
                json_dict = args[0]
            elif len(args) == 0:
                json_dict = _get_args()

            # check all required arguments are present
            if required_args:
                required = set(required_args)
                present = set(json_dict.keys())
                if not required.issubset(present):
                    result = failure(error='Missing arguments.',
                                     required=list(required_args), # set() is not JSONable
                                     present=list(present))
                    return json.dumps(result)

            req = Request(json_dict)

            # if key is not needed OR if it is needed, is present, and is valid,
            # then move forward
            if not validation_required or (validate_callback and validate_callback(req))
               or (validation_callback and validation_callback(req)):
                result = fn(req)
            else:
                result = failure(error='No authorization.')
                return json.dumps(result)

            # if we ran fn(), make sure that it returns a dict with a 'success' key
            # (if the request failed along the way, failure() takes care of that)
            if not 'success' in result:
                raise ValueError('Request does not return a "success" flag.')
            else:
                # tack on some metadata and return
                result['metadata'] = get_metadata(route)
                return json.dumps(result)
        return app.route(route, **kwargs)(wrapper)
    return deco

def get_metadata(path, request):
    meta = {'method': path,
            'return_time': datetime.now().strftime('%m/%d/%Y')}
    return meta

def _get_args():
    from flask import request
    return request.get_json() or request.args

class Request(object):

    def __init__(self, json_dict):
        super(Request, self).__init__()
        new_dict = _copy_dict(json_dict)
        super(Request, self).__setattr__('data', new_dict)

    def __getattribute__(self, value):
        if value == 'as_dict':
            data = super(Request, self).__getattribute__('data')
            return _copy_dict(data)
        try:
            return super(Request, self).__getattribute__('data')[value]
        except KeyError:
            return None
            raise AttributeError("'{cls}' object has no attribute '{attr}'".format(cls=Request.__name__,
                                                                                   attr=value))

    def __setattr__(self, attr, value):
        super(Request, self).__getattribute__('data')[attr] = value

def _copy_dict(dict):
    return {k: v for k, v in dict.iteritems()}
