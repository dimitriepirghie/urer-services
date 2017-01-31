import json
import urllib2

FACEBOOK_APP_ID = '1266953439991986'
FACEBOOK_APP_SECRET = '8cefcc09304059e1139f54f9fb03e20d'


def create_post_url(graph_url):
    post_args = "/posts/?key=value&access_token=" + FACEBOOK_APP_ID + "|" + FACEBOOK_APP_SECRET
    post_url = graph_url + post_args
    return post_url


def create_image_url(graph_url):
    post_args = "/picture/?key=value&access_token=" + FACEBOOK_APP_ID + "|" + FACEBOOK_APP_SECRET
    post_url = graph_url + post_args
    return post_url


def render_to_json(graph_url):
    web_response = urllib2.urlopen(graph_url)
    readable_page = web_response.read()
    json_data = json.loads(readable_page)
    return json_data


def render_normal(graph_url):
    web_response = urllib2.urlopen(graph_url)
    return web_response.geturl() if web_response else ""


def unicode_normalize(text):
    return text.translate({0x2018: 0x27, 0x2019: 0x27, 0x201C: 0x22, 0x201D: 0x22,
                           0xa0: 0x20}).encode('utf-8')


def harvest_facebook(keywords):
    posts = {}
    graph_url = "https://graph.facebook.com/"

    for keyword in keywords:
        current_page = graph_url + keyword

        post_url = create_post_url(current_page)
        json_postdata = render_to_json(post_url)

        if "data" in json_postdata:
            normalized_posts = []
            json_fbposts = json_postdata['data']

            for post in json_fbposts:
                try:
                    normalized_posts.append(unicode_normalize(post["message"]))
                except Exception:
                    pass

            if len(normalized_posts):
                image_url = create_image_url(current_page)
                image_url_result = render_normal(image_url)
                posts[keyword] = {
                    "messages": normalized_posts,
                    "image_url": image_url_result
                }

    return posts
