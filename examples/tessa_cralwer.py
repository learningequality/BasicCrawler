#!/usr/bin/env python
import argparse
import re
from urllib.parse import urljoin, urldefrag


from crawler import BasicCrawler


TESSA_HOME_URL = 'http://www.tessafrica.net/home'   # content is not here though...
TESSA_LANG_URL_MAP = {
    'en': 'http://www.open.edu/openlearncreate/course/view.php?id=2042',
    'fr': 'http://www.open.edu/openlearncreate/course/view.php?id=2046',
    'ar': 'http://www.open.edu/openlearncreate/course/view.php?id=2198',
    'sw': 'http://www.open.edu/openlearncreate/course/view.php?id=2199',
}
SUBPAGE_RE = re.compile('.*mod/subpage/.*')
CONTENT_RE = re.compile('.*mod/oucontent/.*')
RESOURCE_RE = re.compile('.*mod/resource/.*')


class TessaCrawler(BasicCrawler):
    """
    Crawler for the Teacher Education for Sub-Saharan Africa (TESSA) web resources
    hosted on open.edu/openlearncreate/ content management system.
    """
    MAIN_SOURCE_DOMAIN = 'http://www.open.edu'
    START_PAGE = None  # set in __init__
    START_PAGE_CONTEXT = {'kind':'tessa_language_page'}

    SOURCE_DOMAINS = ['http://www.tessafrica.net', 'http://www.open.edu', 'https://www.open.edu']
    IGNORE_URLS = [
        'http://www.open.edu/openlearn/',
        'http://www.open.edu/openlearncreate',
        'http://www.open.edu/openlearncreate/',
        'http://www.open.edu/openlearncreate/my/',
        'http://www.open.edu/openlearncreate/local/ocwactivityreports/',  # My profile
        'http://www.open.edu/openlearncreate/local/ocwcollections/collections.php',
        'http://www.open.edu/openlearncreate/course/index.php',
        'http://www.open.edu/openlearncreate/course/index.php?categoryid=25',   # all collections
        'http://www.open.edu/openlearncreate/course/index.php?categoryid=47',   # TESSA main page = parent for all langs
        'http://www.open.edu/openlearnworks/mod/url/view.php?id=83245',  # OLCreate: TESSA_SHARE TESSA - Share
        'http://www.open.edu/openlearncreate/local/ocwfaqs/faq.php',  # FAQ OpenLearn Create
    ]
    IGNORE_URL_PATTERNS = [
        re.compile('.*openlearncreate/login\.php.*'),
        re.compile('.*local/ocwcreatecourse/.*'),
        re.compile('.*local/ocwfreecourses/.*'),
        re.compile('.*mod/oucontent/olink.php.*'),  # weird kind of internal cross references (cause rescaping of things we alrady have)
        re.compile('.*oucontent/hidetip.php.*'),
    ]

    CRAWLING_STAGE_OUTPUT = 'chefdata/trees/tessa_web_resource_tree.json'




    def __init__(self, *args, lang='en', **kwargs):
        super().__init__(*args, **kwargs)
        self.START_PAGE = TESSA_LANG_URL_MAP[lang]

        # save output for specific lang
        self.CRAWLING_STAGE_OUTPUT = self.CRAWLING_STAGE_OUTPUT.replace('.json', '_'+lang+'.json')

        # ignore main page links for other languages
        other_links = TESSA_LANG_URL_MAP.copy()
        del other_links[lang]
        self.IGNORE_URLS.extend(other_links.values())

        self.kind_handlers = {  # mapping from web resource kinds (user defined) and handlers
            'tessa_language_page': self.on_tessa_language_page,
            'subpage': self.on_subpage,
            'oucontent': self.on_oucontent,
            'resource': self.on_resource,
        }


    def cleanup_url(self, url):
        """
        Removes fragment and query string parameters that falsely make URLs look diffent.
        """
        url = urldefrag(url)[0]
        url = re.sub('&section=\d+(\.\d+)?', '', url)
        url = re.sub('&printable=1', '', url)
        url = re.sub('&content=scxml', '', url)
        url = re.sub('&notifyeditingon=1', '', url)
        url = re.sub('\?forcedownload=1', '', url)
        url = re.sub('&forcedownload=1', '', url)
        return url


    # PAGE HANDLERS
    ############################################################################

    def on_tessa_language_page(self, url, page, context):
        """
        Basic handler that adds current page to parent's children array and adds
        all links on current page to the crawling queue.
        """
        print('Procesing tessa_language_page', url)
        page_dict = dict(
            kind='TessaLangWebRessourceTree',
            url=url,
            title=self.get_title(page),
            children=[],
        )
        page_dict.update(context)

        # attach this page as another child in parent page
        context['parent']['children'].append(page_dict)

        course_content_div = page.find(class_="course-content")
        links = course_content_div.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('href'):
                link_url = self.normalize_href_relto_curpage(link['href'], url)
                if self.should_visit_url(link_url):
                    context = {'parent':page_dict}
                    if SUBPAGE_RE.match(link_url):
                        context.update({'kind':'subpage'})
                        self.enqueue_url_and_context(link_url, context)
                    elif CONTENT_RE.match(link_url):
                        context.update({'kind':'oucontent'})
                        self.enqueue_url_and_context(link_url, context)
                    else:
                        print('Skipping link', link_url, 'on page', url)
            else:
                pass
                # print(i, 'nohref', link)


    def on_subpage(self, url, page, context):
        print('Procesing subpage', url)
        subpage_dict = dict(
            kind='TessaSubpage',
            url=url,
            title=self.get_title(page),
            children=[],
        )
        subpage_dict.update(context)

        # attach this page as another child in parent page
        context['parent']['children'].append(subpage_dict)

        course_content_div = page.find(class_="pagecontent-content")
        links = course_content_div.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('href'):
                link_url = self.normalize_href_relto_curpage(link['href'], url)
                if self.should_visit_url(link_url):
                    context = {'parent':subpage_dict}
                    if SUBPAGE_RE.match(link_url):
                        context.update({'kind':'subpage'})
                        self.enqueue_url_and_context(link_url, context)
                    elif CONTENT_RE.match(link_url):
                        context.update({'kind':'oucontent'})
                        self.enqueue_url_and_context(link_url, context)
                    elif RESOURCE_RE.match(link_url):
                        context.update({'kind':'resource'})
                        self.enqueue_url_and_context(link_url, context)
                    else:
                        print('>>> Skipping link', link_url)
            else:
                pass
                print(i, 'nohref', link)


    def on_oucontent(self, url, page, context):
        print('Procesing oucontent', url, self.get_title(page))
        oucontent_dict = dict(
            kind='TessaContent',
            url=url,
            title=self.get_title(page),
            children=[],
        )
        oucontent_dict.update(context)

        # attach this page as another child in parent page
        context['parent']['children'].append(oucontent_dict)


    def on_resource(self, url, page, context):
        print('Procesing resource', url, self.get_title(page))
        resource_dict = dict(
            kind='TessaResource',
            url=url,
            title=self.get_title(page),
            children=[],
        )
        resource_dict.update(context)

        # attach this resource as another child in parent page
        context['parent']['children'].append(resource_dict)


# CLI
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is the TESSA crawler')
    parser.add_argument('--lang', required=True, help='Which TESSA language to crawl')
    args = parser.parse_args()

    crawler = TessaCrawler(lang=args.lang)
    channel_tree = crawler.crawl(debug=True, limit=500)
    crawler.print_tree(channel_tree)
