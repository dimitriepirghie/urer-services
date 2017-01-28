import json
import os
import threading
import time
from functools import wraps
import random
from logger import logger
import validators
import requests
from flask import Flask, request, make_response, abort
from external_api.GooglePlacesAPI import GooglePlacesAPI, allowed_search_parameters

__author__ = 'Pirghie Dimitrie'
__project__ = 'UReR'

app = Flask(__name__)

api_key = os.environ.get("POIS_API_KEY", None)
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", 'AIzaSyAb1qLl7Q-25BhSAnZWgMJ7YhLz6yZGjWk')


def validate_new_event_request(function):
    @wraps(function)
    def check_json(*args, **kwargs):
        try:
            request_json = json.loads(request.data)

            if 'key' not in request_json or 'response_at' not in request_json or 'request_id' not in request_json:
                logger.error(request.remote_addr + ' called /new_event with invalid json')
                raise ValueError('')

            if api_key and request_json['key'] != api_key:
                logger.error(request.remote_addr + ' called with invalid api key')
                return abort(401, json.dumps({'reason': 'Invalid API Key'}))

        except ValueError as e:
            logger.error(e.message)
            return abort(400, json.dumps({'reason': 'Invalid POST Data'}))
        return function(*args, **kwargs)

    return check_json


def nice_json(arg, status_code):
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response, status_code


def call_google_api(request_json):
    try:
        google_api = GooglePlacesAPI(GOOGLE_PLACES_API_KEY)

        for request_parameter in request_json.copy():
            if request_parameter.strip().lower() not in allowed_search_parameters:
                del request_json[request_parameter]

        places_result = google_api.search(**request_json)
        return places_result
    except Exception as e:
        logger.error('call_google_api' + str(e.message))
        return None


def do_task(request_json):
    """

    :param request_json:
    :return:
    """

    try:
        response_at = request_json['response_at']
        request_id = request_json['request_id']

        logger.info('Try to find recommendation for request with id ' + str(request_id))

        response = call_google_api(request_json=request_json)

        if not validators.url(response_at):
            logger.error("Response at " + str(response_at) + ' not a valid url')
            return

        post_reply = requests.post(response_at, data=json.dumps(response))

        if 200 == post_reply.status_code:
            logger.info('Push request at ' + response_at + ' with id ' + str(request_id) + ' succeeded')

    except requests.exceptions.ConnectionError as e:
        logger.error('Push request at ' + response_at + ' with id ' + str(request_id) + ' failed')
        pass


@app.route('/new_event', methods=['POST'])
@validate_new_event_request
def new_event():
    try:
        request_json = json.loads(request.data)

        thread_do_task = threading.Thread(target=do_task, args=(request_json, ))
        thread_do_task.start()

    except ValueError:
        return nice_json({'reason': 'Invalid POST Data'}, 400)
    return nice_json({'status': 'New event registered'}, 201)


if __name__ == '__main__':
    app_port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=app_port, debug=True)

    """
    request = {'location': '47.171571, 27.574983',
               'radius': 200,
               'type': 'restaurant',
               'request_id': 'bla',
               'response_at': 'bla2'
               }
    do_task(request)
    """


