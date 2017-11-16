#!/usr/bin/env python

from crawler import BasicCrawler


class TakeHomeCrawler(BasicCrawler):
    MAIN_SOURCE_DOMAIN = 'http://chef-take-home-test.learningequality.org'
    START_PAGE = 'http://chef-take-home-test.learningequality.org/'

    SOURCE_DOMAINS = [MAIN_SOURCE_DOMAIN]
    IGNORE_URLS = []
    IGNORE_URL_PATTERNS = []

    CRAWLING_STAGE_OUTPUT = 'chefdata/trees/takehome_web_resource_tree.json'

    rules = []          # contains tuples (path.RE.pattern, handler_function)
    kind_handlers = {}  # mapping from web resource kinds (user defined) and handlers
                        # e.g. {'LesssonWebResource': self.on_lesson, ...}
    # 
    # def on_channel
    #
    #
    # def on_topic




# CLI
################################################################################

if __name__ == '__main__':
    crawler = TakeHomeCrawler()
    channel_tree = crawler.crawl()
    crawler.print_tree(channel_tree)
