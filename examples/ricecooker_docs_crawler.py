#!/usr/bin/env python
import re


from basiccrawler.crawler import BasicCrawler
from basiccrawler.crawler import LOGGER, logging
LOGGER.setLevel(logging.DEBUG)


# PARAMS
################################################################################
START_PAGE = 'https://ricecooker.readthedocs.io/en/latest/index.html'
IGNORE_URLS = [
    re.compile('.*docs.readthedocs.io.*'),
    re.compile('.*readthedocs.org.*'),
]


# CLI
################################################################################

if __name__ == '__main__':
    """
    Crawl a the Learning Equality website at https://learningequality.org
    """
    crawler = BasicCrawler(start_page=START_PAGE)
    crawler.IGNORE_URLS.extend(IGNORE_URLS)
    crawler.CRAWLING_STAGE_OUTPUT = 'chefdata/trees/ricecooker_docs_web_resource_tree.json'
    channel_tree = crawler.crawl(limit=10000)

    crawler.print_tree(channel_tree)
    print('\nOutput web resource tree saved to', crawler.CRAWLING_STAGE_OUTPUT)
