import json
import time
import threading

import feedparser
from concurrent import futures


class Feeder(object):
    # TODO: Implement specific filterting for each category (computer, art, etc.)
    from rss_lists import rss_full_list as __rss_full_list

    __feeds = list()
    __backup_feeds = list()
    __init_feeder = False
    __min_keyword_appearances = 1
    __CRAWLER_THREAD_TIMEOUT = 60 * 60  # from hour in hour

    def __init__(self, keywords):
        super(Feeder, self).__init__()
        self.keywords = keywords
        self.frequency_dict = dict()

        if not self.__init_feeder:  # Kind of singleton
            self.__init_feeder = True
            self.__feed_()

            threading.Thread(target=self.__crawler_thread_).start()

    def filter(self):
        feeds_copy = self.__backup_feeds
        if not feeds_copy:  # If the crawler thread is not running right now...
            feeds_copy = self.__feeds

        for feed in feeds_copy:
            for entry in feed["entries"]:
                for keyword in keywords:
                    if 'summary' not in entry:
                        break

                    frequency = entry['summary'].count(keyword)

                    if frequency >= self.__min_keyword_appearances:
                        d = {
                            'frequency': frequency,
                            'title': entry['title'],
                            'link': entry['link'],
                        }

                        if keyword not in self.frequency_dict:
                            self.frequency_dict[keyword] = [d]
                        else:
                            if d['title'] not in [i['title'] for i in self.frequency_dict[keyword]]:
                                self.frequency_dict[keyword].append(d)

        sorted_dict = dict(sorted(self.frequency_dict.iteritems(), key=lambda x: lambda y: x[y]['frequency'], reverse=True))
        return json.dumps(sorted_dict)

    def __process_future_(self, f):
        feed = f.result()
        self.__feeds.append(feed)

    def __feed_(self):
        with futures.ThreadPoolExecutor(max_workers=8) as executor:
            for rss_site in self.__rss_full_list:
                try:
                    feed = executor.submit(feedparser.parse, rss_site)
                    feed.add_done_callback(self.__process_future_)
                except Exception:
                    pass  # Not interested in

    def __crawler_thread_(self):
        """
        The crawler thread
        """
        while True:
            time.sleep(self.__CRAWLER_THREAD_TIMEOUT)
            self.__backup_feeds = self.__feeds[:]
            self.__feeds[:] = list()
            self.__feed_()
            self.__backup_feeds[:] = list()


if __name__ == "__main__":
    keywords = ["machine learning", "big data"]
    feeder = Feeder(keywords)
    articles = feeder.filter()
    print articles
    # TODO: do whatever you want to do with the json object articles
