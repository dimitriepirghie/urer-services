import json
import os
import threading
from functools import wraps
from logger import logger
import validators
import requests
from flask import Flask, request, make_response, abort
# Our imports
from external_api.GooglePlacesAPI import GooglePlacesAPI, allowed_search_parameters
from nearby.NearByFriends import NearByFriends

__author__ = 'Pirghie Dimitrie'
__project__ = 'UReR'

app = Flask(__name__)
flask_app_context = app.app_context()
flask_app_context.push()

api_key = os.environ.get("POIS_API_KEY", None)
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", 'AIzaSyDOLLvtyMDjnOuc1OrZ51wrAhUN2TLrI2A')


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
    response = make_response(json.dumps(arg, sort_keys=True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response, status_code


def call_google_api(request_json):
    logger.info('call google api with ' + str(request_json))
    try:
        google_api = GooglePlacesAPI(GOOGLE_PLACES_API_KEY)

        for request_parameter in request_json.copy():
            if request_parameter.strip().lower() not in allowed_search_parameters:
                del request_json[request_parameter]

        places_result = google_api.search(**request_json)
        logger.info("Google API Result " + '- too much logs')
        return places_result
    except Exception as e:
        logger.error('call_google_api error' + str(e.message))
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

        response_from_google = call_google_api(request_json=request_json)

        if response_from_google and 'ZERO_RESULTS' in response_from_google:
            logger.info('Do not response, not results from google, request ' + str(request_id))
            return
        elif not response_from_google:
            logger.info('Response from Google None, abort')
            return

        try:
            response_from_google = json.loads(response_from_google)
        except Exception as e:
            logger.info("Response from google not as json, will be as string")

        response = {'request_id': request_id,
                    'result': response_from_google}

        '''if not validators.url(response_at):
            logger.error("Response at " + str(response_at) + ' not a valid url')
            return
        '''

        post_reply = requests.post(response_at, data=json.dumps(response), headers={'Content-type': 'application/json'})

        if 200 == post_reply.status_code:
            logger.info('Push request at ' + response_at + ' with id ' + str(request_id) + ' succeeded')
        else:
            logger.error('Push failed at ' + response_at + ' code ' + str(post_reply.status_code))

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


def do_near_by(near_by_data):
    nearby_friends_handler = NearByFriends(near_by_data)


@app.route('/nearby', methods=['POST'])
def nearby():
    """

    :return:
    """
    # JSON Request example
    """
    {
        "user_id": "1322aa",
        "response_at": "http://urer-client.herokuapp.com/receive/nearbyfriends",
        "location": "47.171571, 27.574983",
        "timestamp": 12312312
    }
    """
    logger.info("Nearby called")
    try:
        nearby_post_data = json.loads(request.data)
        nearby_thread = threading.Thread(target=do_near_by, args=(nearby_post_data, ))
        nearby_thread.start()
    except (ValueError, AttributeError) as e:
        logger.error(e.message)
        return nice_json(json.dumps(e.message), status_code=400)

    return nice_json({'status': 'User location updated'}, 201)

if __name__ == '__main__':
    app_port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=app_port, debug=True, threaded=True)

    """
    request = {'location': '47.171571, 27.574983',
               'radius': 200,
               'type': 'restaurant',
               'request_id': 'bla',
               'response_at': 'bla2'
               }
    do_task(request)
    """
