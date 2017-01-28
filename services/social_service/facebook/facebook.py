from flask import Flask, redirect, url_for, session, request
from flask_oauthlib.client import OAuth, OAuthException


FACEBOOK_APP_ID = '1266953439991986'
FACEBOOK_APP_SECRET = '8cefcc09304059e1139f54f9fb03e20d'


app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)


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


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


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
    me = facebook.get('/me?fields=name,email')
    friends = facebook.get('/me/friends')

    friends_list = str()
    for i in friends.data['data']:
        friends_list += i['name'] + ', '
    friends_list = friends_list[:-2]

    if 'email' not in me.data:
        me.data['email'] = 'Unknown'

    return 'Logged in as name=%s ; Your email is: %s ; Your friends are: %s' % \
        (me.data['name'],
         me.data['email'],
         friends_list)


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
