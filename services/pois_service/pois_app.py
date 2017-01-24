import json
import os

from flask import Flask, request, make_response

app = Flask(__name__)


def nice_json(arg, status_code):
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response, status_code


@app.route('/new_event', methods=['POST'])
def new_event():
    try:
        request_json = json.loads(request.data)
    except ValueError:
        return nice_json({'reason': 'Invalid POST Data'}, 400)
    return nice_json({'status': 'New event registered'}, 201)


if __name__ == '__main__':
    app_port = os.environ.get('PORT', 5001)
    app.run(host='0.0.0.0', port=app_port, debug=True)