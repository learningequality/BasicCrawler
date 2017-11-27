#!/usr/bin/env python

from collections import defaultdict, Counter
import json
import logging
import re
import os
import queue
import time
from urllib.parse import urljoin, urldefrag

from bs4 import BeautifulSoup
import requests
from ricecooker.utils.caching import CacheForeverHeuristic, FileCache, CacheControlAdapter




# LOGGING
################################################################################
logging.getLogger("cachecontrol.controller").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
from ricecooker.config import LOGGER
__logging_handler = logging.StreamHandler()
LOGGER.addHandler(__logging_handler)
LOGGER.setLevel(logging.DEBUG)



# BASE CRAWLER
################################################################################

class BasicCrawler(object):
    """
    Basic web crawler that uses the breadth first search to visit all pages of a
    website starting from the `MAIN_SOURCE_DOMAIN` and browing pages recursively.
    Every page visited is aware of the `parent` (referring page), which makes it
    possible to consturct a web resource tree that can later be used to construct
    a ricecooker json tree, and ultimately a Kolibri channel.
    """
    # Base class proporties
    BASE_IGNORE_URLS = ['javascript:void(0)', '#']
    BASE_IGNORE_URL_PATTERNS = [re.compile('^mailto:.*'), re.compile('^javascript:.*')]
    MEDIA_CONTENT_TYPES = ['application/pdf', 'video/mpeg', 'application/zip',
                           'audio/vorbis', 'audio/mp3', 'audio/mpeg',
                           'image/png', 'image/jpeg', 'image/gif',
                           'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.openxmlformats-officedocument.presentationml.presentation']

    GLOBAL_NAV_THRESHOLD = 0.7
    CRAWLING_STAGE_OUTPUT = 'chefdata/trees/web_resource_tree.json'

    # Subclass attributes
    MAIN_SOURCE_DOMAIN = None   # should be defined by subclass
    SOURCE_DOMAINS = []         # should be defined by subclass
    START_PAGE = None           # should be defined by subclass
    START_PAGE_CONTEXT = {}     # should be defined by subclass
    IGNORE_URLS = []            # should be defined by subclass
    IGNORE_URL_PATTERNS = []    # should be defined by subclass
    rules = []          # contains tuples (url_RE_pattern, handler_function)
    kind_handlers = {}  # mapping from web resource kinds (user defined) and handlers
                        # e.g. {'LesssonWebResource': self.on_lesson, ...}

    # CACHE LOGIC
    SESSION = requests.Session()
    CACHE = FileCache('.webcache')

    # queue used keep track of what pages we should crawl next
    queue = queue.Queue()

    # keep track of how many times a given URL is seen during crawl
    # first time a URL is seen will be automatically followed, but
    # subsequent occureces will record link existence but not recurse
    global_urls_seen_count = defaultdict(int)  # DB of all urls that have ever been seen
    #  { 'http://site.../fullpath?a=b#c': 3, ... }
    urls_visited = {}  # 'http://site.../fullpath?a=b#c' --> cached version of html content


    def __init__(self, main_source_domain=None, start_page=None):
        if main_source_domain:
            if main_source_domain.endswith('/'):
                main_source_domain = main_source_domain[0:-1]
            self.MAIN_SOURCE_DOMAIN = main_source_domain
            if self.MAIN_SOURCE_DOMAIN not in self.SOURCE_DOMAINS:
                self.SOURCE_DOMAINS.append(self.MAIN_SOURCE_DOMAIN)
            self.START_PAGE = self.MAIN_SOURCE_DOMAIN + '/'
        if start_page:
            self.START_PAGE = start_page

        # keep track of broken links
        self.broken_links = []

        forever_adapter= CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=self.CACHE)
        for source_domain in self.SOURCE_DOMAINS:
            self.SESSION.mount(source_domain, forever_adapter)   # TODO: change to less aggressive in final version



    # GENERIC URL HELPERS
    ############################################################################

    def cleanup_url(self, url):
        """
        Removes URL fragment that falsely make URLs look diffent.
        Subclasses can overload this method to perform other URL-normalizations.
        """
        url = urldefrag(url)[0]
        return url

    # def path_to_url(self, path):
    #     """
    #     Returns url from path.
    #     """
    #     if path.startswith('/'):
    #         url = self.MAIN_SOURCE_DOMAIN + path
    #     else:
    #         url = path
    #     return url

    def url_to_path(self, url):
        """
        Remove any of the SOURCE_DOMAINS from url if it starts with one of them.
        """
        for source_domain in self.SOURCE_DOMAINS:
            if url.startswith(source_domain):
                path = url.replace(source_domain, '')
                return path
        return url


    def should_ignore_url(self, url):
        """
        Returns True if `url` matches any of the IGNORE_URL criteria.
        """
        url = self.cleanup_url(url)

        # 1. run through ignore lists
        if url in self.BASE_IGNORE_URLS or url in self.IGNORE_URLS:
            return True
        for pattern in self.BASE_IGNORE_URL_PATTERNS:
            match = pattern.match(url)
            if match:
                return True
        for pattern in self.IGNORE_URL_PATTERNS:
            match = pattern.match(url)
            if match:
                return True

        # 2. check if url is on one of the specified source domains
        found = False
        for source_domain in self.SOURCE_DOMAINS:
            if url.startswith(source_domain):
                found = True
        return not found     # should ignore if not found in SOURCE_DOMAINS list


    def is_media_file(self, url):
        """
        Makes a HEAD request for `url` and reuturns (vertict, head_response),
        where verdict is True if `url` points to a media file (.pdf, .docx, etc.)
        """
        head_response = self.make_request(url, method='HEAD')
        if head_response:
            content_type = head_response.headers.get('content-type', None)
            if not content_type:
                LOGGER.warning('HEAD response does not have `content-type` header. url = ' + url)
                return (False, None)
            if content_type in self.MEDIA_CONTENT_TYPES:
                return (True, head_response)
            else:
                return (False, head_response)
        else:
            LOGGER.warning('HEAD request failed for url ' + url)
            return (False, None)



    # CRAWLING TASK QUEUE API
    ############################################################################
    #
    # queue tasks are tuples (url, context) where
    #  - url (str): which page should be visited
    #  - context (dict): generic container for data associated with url, notably
    #     - `context['parent']` is the web resources dict of the referring page
    #     - `context['kind']` can be used to assign a custom handler, e.g., on_course

    def queue_empty(self):
        return self.queue.empty()

    def get_url_and_context(self):
        return self.queue.get()

    def enqueue_url_and_context(self, url, context, force=False):
        # TODO(ivan): clarify crawl-only-once logic and use of force flag in docs
        url = self.cleanup_url(url)
        if url not in self.global_urls_seen_count.keys() or force:
            # LOGGER.debug('adding to queue:  url=' + url)
            self.queue.put((url, context))
        else:
            pass
            # LOGGER.debug('Not going to crawl url ' + url + 'beacause previously seen.')
        self.global_urls_seen_count[url] += 1



    # BASIC PAGE HANDLER
    ############################################################################

    def on_page(self, url, page, context):
        """
        Basic handler that appends current page to parent's children list and
        adds all links on current page to the crawling queue.
        """
        LOGGER.debug('in on_page ' + url)
        page_dict = dict(
            kind='PageWebResource',
            url=url,
            children=[],
        )
        page_dict.update(context)

        # attach this page as another child in parent page
        context['parent']['children'].append(page_dict)

        links = page.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('href'):
                link_url = urljoin(url, link['href'])
                if self.should_ignore_url(link_url):
                    pass
                    # Use this when debugging to also add links not-followed to output
                    # self.record_ignored_url(link_ulr, page_dict)
                else:
                    self.enqueue_url_and_context(link_url, {'parent':page_dict})
            else:
                pass
                # LOGGER.debug('a with no nohref found ' + str(link))


    # MAIN LOOP
    ############################################################################

    def crawl(self, limit=1000, save_web_resource_tree=True, devmode=True):
        start_url = self.START_PAGE
        channel_dict = dict(
            url='This is a temp. outer container for the crawler channel tree.'
                'Its unique child node is the web root.',
            kind='WEB_RESOURCE_TREE_CONTAINER',
            children=[],
        )
        root_context = {'parent':channel_dict}
        if self.START_PAGE_CONTEXT:
            root_context.update(self.START_PAGE_CONTEXT)
        self.enqueue_url_and_context(start_url, root_context)

        counter = 0
        while not self.queue_empty():

            # 1. GET next url to crawl an its context dict
            original_url, context = self.get_url_and_context()

            # 2. Media files (PDF/ZIP/MP3) and broken link check
            verdict, head_response = self.is_media_file(original_url)
            if head_response is None:
                LOGGER.warning('HEAD ' + original_url + ' did not return response.')

            if verdict == True:
                self.record_media_file_url(context['parent'], original_url, head_response)
                continue

            # 3. Let's go GET that url
            url, page = self.download_page(original_url)
            if page is None:
                LOGGER.warning('GET ' + original_url + ' did not return page.')
                self.record_broken_link_url(context['parent'], original_url)
                continue

            # cache BeatifulSoup parsed html in memory (because RAM is cheap!)
            self.urls_visited[original_url] = page

            # annotate context to keep track of URL befor redirects
            if url != original_url:
                context['original_url'] = original_url


            ##########  HANDLER DISPATCH LOGIC  ################################
            handled = False
            # A. kind-handler based dispatch logic
            if 'kind' in context:
                kind = context['kind']
                if kind in self.kind_handlers:
                    handler = self.kind_handlers[kind]
                    if callable(handler):
                        handler(url, page, context)
                        handled = True
                    elif isinstance(handler, str) and hasattr(self, handler):
                        handler_fn = getattr(self, handler)
                        handler_fn(url, page, context)
                        handled = True
                    else:
                        raise ValueError('Unrecognized handler type', handler, 'Should be method or name of method.')
                else:
                    LOGGER.info('No handler registered for kind ' + str(kind)
                                 + ' so falling back to on_page handler.')

            # B. URL rules handler dispatlogic
            path = url.replace(self.MAIN_SOURCE_DOMAIN, '')    # TODO: redo with urls instead of paths <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            for pat, handler_fn in self.rules:
                if pat.match(path):
                    handler_fn(url, page, context['parent'])
                    handled = True

            # if none of the above caught it, we use the default on_page handler
            if not handled:
                self.on_page(url, page, context)
            ####################################################################

            # limit crawling to 1000 pages unless otherwise told (failsafe default)
            counter += 1
            if limit and counter > limit:
                break


        # remove parent links before output tree
        self.cleanup_web_resource_tree(channel_dict)

        # hoist entire tree one level up to get rid of the tmep. outer container
        channel_dict = channel_dict['children'][0]

        # Save output
        if save_web_resource_tree:
            self.write_web_resource_tree_json(channel_dict)

        # Display debug info
        if devmode:
            self.print_crawler_devmode(channel_dict)

        return channel_dict


    def download_page(self, url, *args, **kwargs):
        """
        Download `url` (following redirects) and soupify response contents.
        Returns (final_url, page) where final_url is URL afrer following redirects.
        """
        response = self.make_request(url, *args, **kwargs)
        if not response:
            return (None, None)
        html = response.content
        page = BeautifulSoup(html, "html.parser")
        LOGGER.debug('Downloaded page ' + str(url) + ' title:' + self.get_title(page))
        return (response.url, page)


    def make_request(self, url, timeout=60, *args, method='GET', **kwargs):
        """
        Failure-resistant HTTP GET/HEAD request helper method.
        """
        retry_count = 0
        max_retries = 5
        while True:
            try:
                response = self.SESSION.request(method, url, *args, timeout=timeout, **kwargs)
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                retry_count += 1
                LOGGER.warning("Connection error ('{msg}'); about to perform retry {count} of {trymax}."
                               .format(msg=str(e), count=retry_count, trymax=max_retries))
                time.sleep(retry_count * 1)
                if retry_count >= max_retries:
                    LOGGER.error("FAILED TO RETRIEVE:" + str(url))
                    return None
        if response.status_code != 200:
            LOGGER.error("ERROR " + str(response.status_code) + ' when getting url=' + url)
            return None
        return response




    # DEFAULT ACTIONS FOR MEDIA FILES AND BROKEN LINKS
    ############################################################################

    def record_media_file_url(self, parent, original_url, head_response):
        """
        Append metadata from `head_response` for media `url` as new child of `parent`.
        """
        url = self.cleanup_url(head_response.url)  # URL after possible redirect
        media_rsrc_dict = dict(
            kind='MediaWebResource',
            url=url,
            parent=parent,
            children=[],
        )
        if url != original_url:
            media_rsrc_dict['original_url'] = original_url
        #
        content_type = head_response.headers.get('content-type', None)
        if content_type:
            media_rsrc_dict['content-type'] = content_type
        # TODO(ivan): resolve content-type to contenty type label using le-utils lookup
        #
        content_disposition = head_response.headers.get('content-disposition', None)
        if content_disposition:
            media_rsrc_dict['content-disposition'] = content_disposition
        #
        content_length = head_response.headers.get('content-length', None)
        if content_length:
            media_rsrc_dict['content-length'] = content_length
        #
        # append as new child of parent
        parent['children'].append(media_rsrc_dict)


    def record_broken_link_url(self, parent, url):
        """
        Record a broken link `url` as new child of `parent`.
        """
        broken_link_dict = dict(
            kind='BrokenLink',
            url=url,
            parent=parent,
            children=[],
        )
        parent['children'].append(broken_link_dict)
        self.broken_links.append(url)

    def record_ignored_url(self, parent, url):
        """
        Record a URL that mathing one of self.IGNORE_URLS as new child of `parent`.
        """
        ignored_url_dict = dict(
            kind='IgnoredUrl',
            url=url,
            parent=parent,
            children=[],
        )
        parent['children'].append(ignored_url_dict)



    # WEB RESOURCE INFO UTILS (CRAWLER DEVMODE)
    ############################################################################

    def print_crawler_devmode(self, channel_tree):
        """
        Craweler devmode info useful during interactive development of the cralwer.
        """
        print('\n\n\n')
        print('#'*80)
        print('# CRAWLER RECOMMENDATIONS BASED ON URLS ENCOUNTERED:')
        print('#'*80)

        print('\n1. These URLs are very common and look like global navigation links:')
        global_nav_candidates = self.infer_gloabal_nav(channel_tree)
        for c in global_nav_candidates['children']:
            print('  - ', c['url'])

        print('\n2. These are common path fragments found in URLs paths, so could correspond to site struture:')
        fragments_tuples = self.infer_tree_structure(channel_tree)
        for fpath, fcount in fragments_tuples:
            print('  - ', str(fcount), 'urls on site start with ', '/'+fpath)

        if len(self.broken_links) > 0:
            print('\n3. These are broken links --- you might want to add them to IGNORE_URLS')
            print(self.broken_links)

        print('\n')
        print('#'*80)
        print('\n\n')


    def infer_tree_structure(self, tree_root, show_top=10):
        """
        Walk web resource tree and look for patterns in urls.
        Print the top 10 occurence of subpaths that are common to multiple URLs.
        E.g. if we see a lot of URLs like /pat/smth1 /pat/smth2 /pat/smth3, we'll
        identify `/pat` as a candidate for site structure: Returns ['/pat', ...]
        """
        # Get URLs
        unique_urls = set()
        def recusive_visit_extract_urls(subtree):
            url = subtree['url']
            if url not in unique_urls:
                unique_urls.add(url)
            for child in subtree['children']:
                recusive_visit_extract_urls(child)
        recusive_visit_extract_urls(tree_root)

        # Build path trie
        subpath_trie = {}
        def _add_parts_here(path_parts, here):
            if not path_parts:
                return
            else:
                part = path_parts.pop(0)
                if part not in here.keys():
                    here[part] = {}
                    _add_parts_here(path_parts, here[part])
                else:
                    _add_parts_here(path_parts, here[part])
        for url in unique_urls:
            path = self.url_to_path(url)
            path = path.split('?')[0]  # rm query string
            path_parts = path.split('/')[1:]
            _add_parts_here(path_parts, subpath_trie)

        # annotate with counts
        def _recusive_count_children(here):
            if not here.keys():
                return 1
            count = 0
            for subpath in here.keys():
                count += _recusive_count_children(here[subpath])
            return count

        path_count_tuples = []
        for path, subtrie in subpath_trie.items():
            count = _recusive_count_children(subtrie)
            path_count_tuples.append( (path, count) )

        # top 10 sorted by count
        sorted_path_count_tuples = sorted(path_count_tuples, key=lambda t: t[1], reverse=True)
        return sorted_path_count_tuples[0:show_top]


    def compute_subtree_stats(self, subtree, counter=None):
        """
        Recusively compute counts of different `kind` web sesources in subtree.
        """
        if counter is None:
            counter = Counter()
            # don't count subtree itself, only its children
        else:
            counter[subtree['kind']] += 1
        if 'children' in subtree:
            for child in subtree['children']:
                self.compute_subtree_stats(child, counter=counter)
        return counter

    def print_tree(self, tree_root, print_depth=3, hide_keys=[]):
        """
        Print contents of web resource tree starting at `tree_root`.
        """
        def print_web_resource_node(node, depth=1):
            INDENT_BY = 3
            extra_attrs = ''
            if node is None:
                print('Encountered a None node in print_web_resource_node')
                return
            if 'kind' in node:
                extra_attrs = ' ('+node['kind']+') '
            path = self.url_to_path(node['url'])  # print paths instead of full URLs
            print(' '*INDENT_BY*depth + '  -', 'path:', path, extra_attrs)
            if depth < print_depth:                 # recurse and print children
                if node['children']:
                    print(' '*INDENT_BY*depth + '   ', 'children:')
                    for child in node['children']:
                        print_web_resource_node(child, depth=depth+1)
            else:                                    # print only summary counts
                counts = self.compute_subtree_stats(node)
                if counts:
                    counts_str = str(counts).replace('Counter', '').strip('()')
                    print(' '*INDENT_BY*depth + '   ', 'children counts:', counts_str)
        print_web_resource_node(tree_root)


    def infer_gloabal_nav(self, tree_root, debug=False):
        """
        Returns a list of web resources that are likely to be global nav links.
        """
        global_nav_nodes = dict(
            url=self.MAIN_SOURCE_DOMAIN,
            kind='GlobalNavLinks',
            children=[],
        )

        # 1. infer global nav URLs based on total seen count / total pages visited
        total_urls_seen_count = len(self.urls_visited.keys())

        def _is_likely_global_nav(url):
            """
            Returns True if `url` is likely a global nav link based on how often seen in pages.
            """
            seen_count = self.global_urls_seen_count[url]
            if debug:
                LOGGER.debug('seen_count/total_urls_seen_count='
                              + str(float(seen_count)/total_urls_seen_count)
                              + '=' + str(seen_count) + '/' + str(total_urls_seen_count)
                              + self.url_to_path(url))
            # if previously determined to be a global nav link
            for global_nav_resource in global_nav_nodes['children']:
                if url == global_nav_resource['url']:
                    return True
            # if new link that is seen a lot
            if float(seen_count)/total_urls_seen_count > self.GLOBAL_NAV_THRESHOLD:
                return True
            return False

        def recusive_visit_find_global_nav_children(subtree):
            for child in subtree['children']:
                child_url = child['url']
                if len(child['children'])== 0 and _is_likely_global_nav(child_url):
                    LOGGER.debug('Found candidate for global nav url=' + str(child_url)
                                  + 'adding to global_nav_nodes')
                    global_nav_resource = dict(
                        kind='GlobalNavLink',
                        url=child_url,
                    )
                    global_nav_resource.update(child)
                    global_nav_nodes['children'].append(global_nav_resource)
                # recurse
                recusive_visit_find_global_nav_children(child)

        recusive_visit_find_global_nav_children(tree_root)
        return global_nav_nodes


    def remove_global_nav(self, tree_root, global_nav_nodes):
        """
        Walks web resource tree and removes all web resources whose URLs match
        nodes in global_nav_nodes['children'].
        This method is a helper for debugging. Your production crawler should use
        `self.IGNORE_URLS` to remove global nav links so won't crawl them at all.
        """
        global_nav_urls = [d['url'] for d in global_nav_nodes['children']]
        def _recusive_visit_rm_global_nav_children(subtree):
            newchildren = []
            for child in subtree['children']:
                child_url = child['url']
                if len(child['children'])== 0 and child_url in global_nav_urls:
                    LOGGER.info('Removing global nav url =' + child_url)
                else:
                    clean_child = _recusive_visit_rm_global_nav_children(child)
                    newchildren.append(clean_child)
            subtree['children'] = newchildren
            return subtree
        _recusive_visit_rm_global_nav_children(tree_root)


    def cleanup_web_resource_tree(self, tree_root):
        """
        Remove nodes' parent links (otherwise tree is not json serializable).
        """
        def cleanup_subtree(subtree):
            if 'parent' in subtree:
                del subtree['parent']
            for child in subtree['children']:
                cleanup_subtree(child)
        cleanup_subtree(tree_root)
        return tree_root



    # TEXT HELPERS
    ############################################################################

    def get_text(element):
        """
        Extract text contents of `element`, normalizing newlines to spaces and stripping.
        """
        if element is None:
            return ''
        else:
            return element.get_text().replace('\r', '').replace('\n', ' ').strip()

    def get_title(self, page):
        title = ''
        head_el = page.find('head')
        if head_el:
            title_el = head_el.find('title')
            if title_el:
                title = title_el.get_text().strip()
        return title




    # OUTPUT JSON
    ############################################################################

    def write_web_resource_tree_json(self, channel_dict):
        destpath = self.CRAWLING_STAGE_OUTPUT
        parent_dir, _ = os.path.split(destpath)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(destpath, 'w') as wrt_file:
            json.dump(channel_dict, wrt_file, indent=2)



# CLI
################################################################################

if __name__ == '__main__':
    crawler = BasicCrawler(
            main_source_domain='http://chef-take-home-test.learningequality.org',
            start_page='http://chef-take-home-test.learningequality.org/')
    crawler.CRAWLING_STAGE_OUTPUT = 'chefdata/trees/takehome_web_resource_tree.json'
    channel_tree = crawler.crawl()
    crawler.print_tree(channel_tree)

