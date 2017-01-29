import json
import time
import threading

import feedparser
from concurrent import futures
from flask import Flask, request, abort

from rss_lists import rss_full_list as __rss_full_list

app = Flask(__name__)

__feeds_ = list()
__backup_feeds = list()
__min_keyword_appearances = 1
__CRAWLER_THREAD_TIMEOUT = 60 * 60  # from hour in hour


def __process_future_(f):
    feed = f.result()
    __feeds_.append(feed)


def __feed_():
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        for rss_site in __rss_full_list:
            try:
                feed = executor.submit(feedparser.parse, rss_site)
                feed.add_done_callback(__process_future_)
            except Exception:
                pass  # Not interested in


def __crawler_thread_():
    """
    The crawler thread
    """
    while True:
        time.sleep(__CRAWLER_THREAD_TIMEOUT)
        __backup_feeds[:] = __feeds_[:]
        __feeds_[:] = list()
        __feed_()
        __backup_feeds[:] = list()


# TODO: Implement specific filterting for each category (computer, art, etc.)
def filter(keywords):
    feeds_copy = __backup_feeds
    if not feeds_copy:  # If the crawler thread is not running right now...
        feeds_copy = __feeds_

    frequency_dict = dict()

    for feed in feeds_copy:
        for entry in feed["entries"]:
            for keyword in keywords:
                if 'summary' not in entry:
                    break

                frequency = entry['summary'].count(keyword)

                if frequency >= __min_keyword_appearances:
                    d = {
                        # 'frequency': frequency,
                        'title': entry['title'],
                        'description': 0,
                        'image': 0,
                        'from': 0,
                        'link': entry['link'],
                    }

                    if keyword not in frequency_dict:
                        frequency_dict[keyword] = [d]
                    else:
                        if d['title'] not in [i['title'] for i in frequency_dict[keyword]]:
                            frequency_dict[keyword].append(d)

    sorted_dict = dict(sorted(frequency_dict.iteritems(), key=lambda x: lambda y: x[y]['frequency'], reverse=True))
    return json.dumps(sorted_dict)


@app.route('/feeder', methods=['POST'])
def feeder():
    if not request.json:
        abort(400)

    if 'user_id' not in request.json or 'keywords' not in request.json:
        abort(422)  # The 422 (Unprocessable Entity) status code means the server understands the content type of the request entity (hence a 415(Unsupported Media Type) status code is inappropriate), and the syntax of the request entity is correct (thus a 400 (Bad Request) status code is inappropriate) but was unable to process the contained instructions. For example, this error condition may occur if an XML request body contains well-formed (i.e., syntactically correct), but semantically erroneous, XML instructions.

    return filter(request.json["keywords"])


if __name__ == "__main__":
    __feed_()
    threading.Thread(target=__crawler_thread_).start()

    app_port = int(__import__("os").environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=app_port, debug=True, threaded=True)
