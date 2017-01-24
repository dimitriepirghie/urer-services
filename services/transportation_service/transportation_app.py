from flask import Flask, request, make_response, abort
import json
import os
import time
import requests
from functools import wraps
import threading
import random
from logger import logger
import validators


def validate_new_event_request(function):
    @wraps(function)
    def check_json(*args, **kwargs):
        try:
            request_json = json.loads(request.data)

            if 'key' not in request_json or 'response_at' not in request_json or 'request_id' not in request_json:
                logger.error(request.remote_addr + ' called /new_event with invalid json')
                raise ValueError('')

        except ValueError as e:
            logger.error(e.message)
            return abort(400, json.dumps({'reason': 'Invalid POST Data'}))
        return function(*args, **kwargs)

    return check_json

app = Flask(__name__)


def nice_json(arg, status_code):
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response, status_code


def do_task(request_json):
    """

    :param request_json:
    :return:
    """

    try:
        response_at = request_json['response_at']
        request_id = request_json['request_id']

        logger.info('Try to find recommendation for request with id ' + str(request_id))

        heavy_load_time = random.randint(3, 20)
        logger.info('Find recommendation estimented time ' + str(heavy_load_time))
        time.sleep(heavy_load_time)

        response = {'request_id': request_id,
                    'transportation': ['transportation_1', 'transportation_2'] }

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
def new_event():
    try:
        request_json = json.loads(request.data)

        thread_do_task = threading.Thread(target=do_task, args=(request_json, ))
        thread_do_task.start()

    except ValueError:
        return nice_json({'reason': 'Invalid POST Data'}, 400)
    return nice_json({'status': 'New event registered'}, 201)

if __name__ == '__main__':
    app_port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=app_port, debug=True)