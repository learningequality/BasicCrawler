#!/usr/bin/env python
from urllib.parse import urljoin

from basiccrawler.crawler import BasicCrawler
from basiccrawler.crawler import LOGGER, logging
LOGGER.setLevel(logging.DEBUG)



# PARAMS
################################################################################
START_PAGE = 'http://chef-take-home-test.learningequality.org/'
IGNORE_URLS = []




# CUSTOM CRAWLER EXAMPLE
################################################################################

class TakeHomeCrawler(BasicCrawler):
    MAIN_SOURCE_DOMAIN = 'http://chef-take-home-test.learningequality.org'
    START_PAGE_CONTEXT = {'kind':'channel'}

    SOURCE_DOMAINS = [MAIN_SOURCE_DOMAIN]
    IGNORE_URLS = []

    CRAWLING_STAGE_OUTPUT = 'chefdata/trees/takehome_web_resource_tree.json'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind_handlers = {   # mapping from web resource kinds (user defined) and handlers
            'channel': self.on_channel_or_topic,
            'topic': self.on_channel_or_topic,
            'audio': self.on_content,
            'video': self.on_content,
            'document': self.on_content,
        }


    def on_channel_or_topic(self, url, page, context):
        """
        Enqueue for crawling all the links on the current page.
        Works for channel root and topic nodes.
        """
        channel_dict = context
        channel_dict.update(dict(
            url=url,
            children=[],
        ))

        # attach this page as another child in parent page
        channel_dict['parent']['children'].append(channel_dict)

        maincontent = page.find('div', {'class': 'maincontent'})

        children_bs = maincontent.find_all('li', {'class': lambda x: x.endswith('-kind')})  # topic-kind, audio-kind, etc.

        for child in children_bs:
            child_href = child.find('a')['href']
            child_url = urljoin(url, child_href)

            # figure out what kind the link is...
            kind = None
            for x in child['class']:
                if x.endswith('-kind'):
                    kind = x.replace('-kind', '')
            if not kind:
                raise ValueError('No kind found!')

            # add to crawling queue
            if not self.should_ignore_url(child_url):
                child_context = dict(
                    kind=kind,
                    parent=channel_dict,
                )
                self.enqueue_url_and_context(child_url, child_context)
            else:
                print('Skipping child_href', child_href)
                pass


    def on_content(self, url, page, context):
        channel_dict = dict(
            url=url,
            children=[],
        )
        channel_dict.update(context)

        # attach this page as another child in parent page
        context['parent']['children'].append(channel_dict)



# CLI
################################################################################

if __name__ == '__main__':
    """
    Crawl a fake content site at http://chef-take-home-test.learningequality.org
    """
    crawler = TakeHomeCrawler(start_page=START_PAGE)
    crawler.IGNORE_URLS.extend(IGNORE_URLS)
    # try also basic-version with no custom logic:
    # crawler = BasicCrawler(start_page='http://chef-take-home-test.learningequality.org/')
    channel_tree = crawler.crawl()

    crawler.print_tree(channel_tree)
    print('\nOutput web resource tree saved to', crawler.CRAWLING_STAGE_OUTPUT)


