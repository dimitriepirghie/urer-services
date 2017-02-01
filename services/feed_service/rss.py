import re
import time
import threading
import traceback
from time import gmtime, strftime

import feedparser
from concurrent import futures
from flask import Flask, request, abort, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON, POST, GET  # , POSTDIRECTLY

from rss_lists import rss_full_list as __rss_full_list

ENDPOINT_URL = "https://dydra.com/dimavascan94/test/sparql"
# ENDPOINT_URL = "https://dydra.com/dimavascan94/urer/sparql"

sparql = SPARQLWrapper(ENDPOINT_URL)
sparql.setReturnFormat(JSON)
sparql.setHTTPAuth('Basic')
sparql.setCredentials('dimavascan94', 'taipwadeurer')
# sparql.setQuery("""
#    select * where { { graph ?g {?s ?p ?o} } union {?s ?p ?o} }
# """)
# results = sparql.query().convert()

app = Flask(__name__)

__feeds_ = list()
__backup_feeds = list()
__min_keyword_appearances = 1
__CRAWLER_THREAD_TIMEOUT = 60 * 60  # from hour in hour

tag_regexp = re.compile('<.*>')


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


def set_select_query_graph():
    if "urer" in ENDPOINT_URL:
        return "FROM <https://urrer.me/users>"

    return ""


def set_insert_query_graph(query):
    if "urer" in ENDPOINT_URL:
        return """
            GRAPH <https://urrer.me/users> {
                %s
            }
        """ % (query)
    else:
        return "%s" % (query)


# TODO: Implement specific filtering for each category (computer, art, etc.)
def feed_articles(user_id):
    feeds_copy = __backup_feeds
    if not feeds_copy:  # If the crawler thread is not running right now...
        feeds_copy = __feeds_

    frequency_dict = dict()

    sparql.setMethod(GET)
    sparql.setQuery("""
        PREFIX wi: <http://xmlns.notu.be/wi#>
        SELECT ?interest ?weight
        %s
        WHERE {
            '%s' wi:preference ?uniqueInterestID.
            ?uniqueInterestID wi:topic ?interest;
                              wi:weight ?weight.
        }
    """ % (set_select_query_graph(), user_id))

    results = sparql.query().convert()
    keywords = [i["interest"]["value"] for i in results["results"]["bindings"]]
    weights = [int(i["weight"]["value"]) for i in results["results"]["bindings"]]

    sparql.setMethod(GET)
    sparql.setQuery("""
        SELECT ?feedLink ?title ?description ?creationDate ?sourceLink ?attachment ?interest ?dismissed
        %s
        WHERE {
                ?feedLink rdf:type sioc:Post;
                            sioc:has_creator '%s';
                            dcterms:title ?title;
                            dc:description ?description;
                            dcterms:created ?creationDate;
                            dc:source ?sourceLink;
                            sioc:attachment ?attachment;
                            sioc:topic ?interest;
                OPTIONAL { ?y sioc:has_modifier '%s'; . FILTER (?feedLink = ?y) . }
                FILTER ( !BOUND(?y) )
             }

    """ % (set_select_query_graph(), user_id, user_id))

    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        keyword = result["interest"]["value"]
        d = {
            "link": result["feedLink"]["value"],
            "title": result["title"]["value"],
            "description": result["description"]["value"],
            # weight?
            "creation_time": result["creationDate"]["value"],
            "from": result["sourceLink"]["value"],
            "image": result["attachment"]["value"],
        }
        if keyword not in frequency_dict:
            frequency_dict[keyword] = [d]
        else:
            frequency_dict[keyword].append(d)

    for feed in feeds_copy:
        for entry in feed["entries"]:
            already_exists = False
            for keyword in list(frequency_dict):  # We need a copy of it
                if already_exists:
                    break

                for index, item in enumerate(frequency_dict[keyword]):
                    if item['link'] == entry["link"]:
                        if len(frequency_dict[keyword]) == 1:
                            del frequency_dict[keyword]
                        else:
                            del frequency_dict[keyword][index]

                        already_exists = True
                        break

            if already_exists:
                continue

            try:
                for idx, keyword in enumerate(keywords):
                    d = {
                        "description": entry['title'],
                    }
                    if 'summary' not in entry:
                        splitted_words = keyword.split(' ')
                        frequency = 0
                        for word in splitted_words:
                            word_list = [word.lower(), word.upper(), word.capitalize()]
                            frequency += sum(entry['title'].count(i) for i in word_list)

                        # We couldn't find half of the words in title, neither
                        if frequency < len(splitted_words) / 2 + 1:
                            break
                        # __import__("sys").stderr.write("keyword %s, title %s, frequency %d, len(splitted_words) %d" % (
                        #     keyword, entry["title"], frequency, len(splitted_words)
                        # ))
                    else:
                        summary = entry['summary']
                        if len(summary) < 10 or tag_regexp.search(summary):
                            break

                        keyword_list = [keyword.lower(), keyword.upper(), keyword.capitalize()]
                        frequency = sum(summary.count(i) for i in keyword_list)
                        if frequency < __min_keyword_appearances:
                            break

                        # __import__("sys").stderr.write("keyword %s, summary %s, frequency %d" % (
                        #     keyword, summary, frequency
                        # ))
                        d.update({"description": summary})

                    d.update({
                        # 'frequency': frequency,
                        'title': entry['title'],
                        'link': entry['link'],
                        'weight': weights[idx],
                        'creation_time': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    })

                    # d['published_time'] = entry.get('published') or entry.get('updated')  # or None :)
                    d['from'] = entry.get('source', {}).get('href', ur"UReR")

                    try:
                        d['image'] = entry['media_content'][0]['url']
                    except:
                        try:
                            d['image'] = feed['feed']['image']['href']
                        except:
                            try:
                                if len(entry['links'] > 1):
                                    for i in entry['links']:
                                        if 'type' in i and 'image' in i['type']:
                                            d['image'] = i['href']
                                            break  # Found one image
                            except:
                                d['image'] = ur"https://cdn4.iconfinder.com/data/icons/hiba-vol-3/512/description-512.png"

                    if keyword not in frequency_dict:
                        frequency_dict[keyword] = [d]
                    else:
                        if d['title'] not in [i['title'] for i in frequency_dict[keyword]]:  # Don't include duplicates
                            frequency_dict[keyword].append(d)

            except:
                traceback.print_exc()

    if len(frequency_dict):
        try:
            sparql.setMethod(GET)
            sparql.setQuery("""
                SELECT ?feedLink ?dismissed
                %s
                WHERE {
                        ?feedLink rdf:type sioc:Post;
                                    sioc:has_creator '%s';
                        OPTIONAL { ?y sioc:has_modifier '%s'; . FILTER (?feedLink = ?y) . }
                        FILTER ( BOUND(?y) )
                     }
            """ % (set_select_query_graph(), user_id, user_id))

            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                for keyword in list(frequency_dict):  # We need a copy of it
                    for index, item in enumerate(frequency_dict[keyword]):
                        if item['link'] == result["feedLink"]["value"]:
                            if len(frequency_dict[keyword]) == 1:
                                del frequency_dict[keyword]
                            else:
                                del frequency_dict[keyword][index]

                            break

            # pp = __import__("pprint").PrettyPrinter(indent=2, stream=__import__("sys").stderr)
            # pp.pprint(frequency_dict)
            # frequency_dict = filter(lambda x: lambda y: x[y] not in seen_articles, frequency_dict)
            # pp.pprint(frequency_dict)
            if len(frequency_dict):  # We have at least one new article for the user_id
                query = ""
                for key, values in frequency_dict.iteritems():
                    for item in values:
                        query += """
                        <%s> rdf:type sioc:Post;
                                dcterms:title '%s';
                                sioc:has_creator '%s';
                                dc:description '%s';
                                dcterms:created '%s';
                                dc:source '%s';
                                sioc:attachment '%s';
                                sioc:topic '%s'.
                        """ % (
                            # Convert to unicode no matter if it's already unicode, because these can be None too...
                            unicode(item["link"]).replace('\\', '\\\\').replace('\'', '\\\''),
                            unicode(item["title"]).replace('\\', '\\\\').replace('\'', '\\\''),
                            user_id,
                            unicode(item["description"]).replace('\\', '\\\\').replace('\'', '\\\''),
                            item["creation_time"],
                            unicode(item["from"]).replace('\\', '\\\\').replace('\'', '\\\''),
                            unicode(item["image"]).replace('\\', '\\\\').replace('\'', '\\\''),
                            unicode(key).replace('\\', '\\\\').replace('\'', '\\\''),
                        )
                        # __import__("sys").stderr.write(unicode(item["from"]).replace('\\', '\\\\').replace('\'', '\\\'') if (item["from"]) is not None and item["from"] != "" else ur"UReR")

                # sparql.setRequestMethod(POSTDIRECTLY)
                sparql.setMethod(POST)
                sparql.setQuery("""
                    INSERT DATA
                    {
                        %s
                    }""" % (set_insert_query_graph(query)))
                sparql.query()
        except:
            traceback.print_exc()

    sorted_dict = dict(sorted(frequency_dict.iteritems(),
                              key=lambda x: lambda y: x[y]['weight'], reverse=True))

    return jsonify(sorted_dict)  # jsonify formats formats json and add Content-Type: plain-text/json


@app.route('/feeder/<string:user_id>', methods=['GET'])
def feeder(user_id):
    # if not request.json:
    #     abort(400)

    # if 'user_id' not in request.json:
    #     abort(422)  # The 422 (Unprocessable Entity) status code means the server understands the content type of the request entity (hence a 415(Unsupported Media Type) status code is inappropriate), and the syntax of the request entity is correct (thus a 400 (Bad Request) status code is inappropriate) but was unable to process the contained instructions. For example, this error condition may occur if an XML request body contains well-formed (i.e., syntactically correct), but semantically erroneous, XML instructions.

    # return feed_articles(request.json['user_id'])
    if not user_id:
        abort(400)

    return feed_articles(user_id)


if __name__ == "__main__":
    threading.Thread(target=__feed_).start()
    threading.Thread(target=__crawler_thread_).start()

    app_port = int(__import__("os").environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=app_port, debug=True)
