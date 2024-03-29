from __future__ import print_function
from flask import Flask, redirect, url_for, session, request, abort, jsonify, current_app, make_response
from flask_oauthlib.client import OAuth, OAuthException
from SPARQLWrapper import SPARQLWrapper, JSON, POST, GET
from RDFQueries import facebook_link_account_query, facebook_select_user_by_fb_id, facebook_insert_follow
import harvest_facebook as harvest_fb
from datetime import timedelta
from functools import update_wrapper

FACEBOOK_APP_ID = '1266953439991986'
FACEBOOK_APP_SECRET = '8cefcc09304059e1139f54f9fb03e20d'


app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

sparql = SPARQLWrapper("https://dydra.com/dimavascan94/urer/sparql")
# sparql = SPARQLWrapper("https://dydra.com/dimavascan94/test/sparql")
sparql.setReturnFormat(JSON)
sparql.setHTTPAuth('Basic')
sparql.setCredentials('dimavascan94', 'taipwadeurer')


"""
    Scope:
        - email (user's email)
        - user_friends (user's list of friends using the same app)
        - public_profile (user's details)
            id
            cover
            name
            first_name
            last_name
            age_range
            link
            gender
            locale
            picture
            timezone
            updated_time
            verified
"""
facebook = oauth.remote_app(
    'facebook',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={
        'scope': 'email,\
                  public_profile,\
                  user_friends'
    },
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.after_request
def after_request_cross_origin(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    return response


# TODO: Check methods only to POST
@app.route('/facebook/<urer_uuid>')# , methods=['POST'])
def index(urer_uuid):
    print('Facebook login request ' + str(urer_uuid))
    if urer_uuid:
        facebook.urer_uuid = urer_uuid
        return redirect(url_for('login'))
    else:
        abort(422)


@app.route('/login')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    facebook_authorization = facebook.authorize(callback=callback)
    return facebook_authorization


# http://flask.pocoo.org/snippets/56/
@app.route('/facebook/interests', methods=["POST"])
# @crossdomain(origin='*', headers=["Access-Control-Allow-Headers"])
def interests():
    if not request.json:
        abort(400)

    if 'interests' not in request.json:
        abort(422)  # The 422 (Unprocessable Entity) status code means the server understands the content type of the request entity (hence a 415(Unsupported Media Type) status code is inappropriate), and the syntax of the request entity is correct (thus a 400 (Bad Request) status code is inappropriate) but was unable to process the contained instructions. For example, this error condition may occur if an XML request body contains well-formed (i.e., syntactically correct), but semantically erroneous, XML instructions.

    return jsonify(harvest_fb.harvest_facebook(request.json["interests"]))


def insert_follow(urrer_id_me, urrer_id_friend):
    query_string = facebook_insert_follow(urrer_id_me, urrer_id_friend)
    try:
        sparql.setMethod(POST)
        sparql.setQuery(query_string)
        query_result = sparql.query()

        if query_result.response.code == 200:
            print('Follows insert  ok ' + str(urrer_id_me) + ' <->' + urrer_id_friend)
        else:
            print('Facebook insert error')

    except Exception as e:
        print(e.message)
    pass

    query_string = facebook_insert_follow(urrer_id_friend, urrer_id_me)
    try:
        sparql.setMethod(POST)
        sparql.setQuery(query_string)
        query_result = sparql.query()

        if query_result.response.code == 200:
            print('Follows insert  ok ' + str(urrer_id_friend) + ' <->' + urrer_id_me)
        else:
            print('Facebook insert error')

    except Exception as e:
        print(e.message)
    pass


def insert_friends(friends_list, my_urrer_id):
    print("Search facebook friends on urer")
    for friend in friends_list:
        print('Friend:')
        print(friend)
        sparql.setMethod(GET)
        select_user_by_fb_id = facebook_select_user_by_fb_id(friend['id'])
        print("Query - " + select_user_by_fb_id)
        sparql.setQuery(select_user_by_fb_id)
        query_result = sparql.query()
        result_converted = query_result.convert()

        try:
            print("Search urer id for friends " + str(friend['name']))
            if len(result_converted["results"]["bindings"]):
                friend_urrer_id = result_converted["results"]["bindings"][0]['uniqueId']['value']
                print("Found urer id for " + friend['name'] + ' with urer id ' + friend_urrer_id)
                insert_follow(my_urrer_id, friend_urrer_id)
            else:
                print("Search urer id not found ")

        except Exception as e:
            print(e.message)

    pass


def insert_facebook_user(user_data, urer_uuid):
    """

    :param user_data:
    :param urer_uuid:
    :return:
    """
    rdf_unique_top = '<https://facebook.com/' + str(user_data['id']) + '>'

    query_string = facebook_link_account_query(rdf_unique_top_string=rdf_unique_top, urrer_uuid=urer_uuid,
                                               fb_user_name=user_data['name'], fb_user_id=user_data['id'],
                                               fb_user_email=user_data['email'],
                                               fb_user_profile_picture=user_data['picture']['data']['url'])
    try:
        sparql.setMethod(POST)
        sparql.setQuery(query_string)
        query_result = sparql.query()

        if query_result.response.code == 200:
            print('Facebook insert ok ' + str(user_data['name'].encode("ascii", "ignore")) + ' urer: ' + urer_uuid)
        else:
            print('Facebook insert error')

    except Exception as e:
        print(e.message)
    pass


@app.route('/login/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me?fields=name,email,picture')
    if 'email' not in me.data:
        me.data['email'] = 'Unknown'

    if me.status == 200:
        insert_facebook_user(user_data=me.data, urer_uuid=facebook.urer_uuid)

    friends = facebook.get('/me/friends')
    insert_friends(friends.data['data'], my_urrer_id=facebook.urer_uuid)

    # friends_list = str()
    # for i in friends.data['data']:
    #     friends_list += i['name'] + ', '
    # friends_list = friends_list[:-2]

    """print('Logged in as name=%s ; Your email is: %s ; Your friends are: %s' % \
          (me.data['name'],
           me.data['email'],
           friends_list))
    """
    return redirect('http://urrer.me')


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
