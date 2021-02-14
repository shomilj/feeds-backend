from flask import escape, jsonify
from algos import api

def api_india(request):
    return query_tweets(request=request)

def query_tweets(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request_json and 'algo' in request_json and 'keyword' in request_json:
        algo, keyword = request_json['algo'], request_json['keyword']
        try:
            return api(algo, keyword)
        except Exception as e:
            return 'error:' + str(e)
    else:
        return escape('error: missing parameters')
