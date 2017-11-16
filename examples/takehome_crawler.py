#!/usr/bin/env python

from urllib.parse import urljoin

from crawler import BasicCrawler


class TakeHomeCrawler(BasicCrawler):
    MAIN_SOURCE_DOMAIN = 'http://chef-take-home-test.learningequality.org'
    START_PAGE = 'http://chef-take-home-test.learningequality.org/'
    START_PAGE_CONTEXT = {'kind':'channel'}

    SOURCE_DOMAINS = [MAIN_SOURCE_DOMAIN]
    IGNORE_URLS = []
    IGNORE_URL_PATTERNS = []

    CRAWLING_STAGE_OUTPUT = 'chefdata/trees/takehome_web_resource_tree.json'

    def __init__(self, *args, **kwargs):
        print('in subclass __init__')
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
        Enqueue for crawling all the links on the current page. Works for channel root and topic nodes.
        """
        print('in on_channel')
        channel_dict = context
        channel_dict.update(dict(
            url=url,
            children=[],
        ))

        # attach this page as another child in parent page
        channel_dict['parent']['children'].append(channel_dict)

        maincontent = page.find('div', {'class': 'maincontent'})

        children = []
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
            if self.should_visit_url(child_url):
                child_context = dict(
                    kind=kind,
                    parent=channel_dict,
                )
                self.enqueue_url_and_context(child_url, child_context)
            else:
                print('Skipping child_href', child_href)
                pass

    def on_content(self, url, page, context):
        print('in on_content')
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
    crawler = TakeHomeCrawler()
    channel_tree = crawler.crawl()
    crawler.print_tree(channel_tree)
