#!/usr/bin/env python
from collections import defaultdict
import json
import re

# GET pages over HTTP
import requests
from ricecooker.utils.caching import CacheForeverHeuristic, FileCache, CacheControlAdapter
import queue

# parse HTML
from bs4 import BeautifulSoup


from le_utils.constants import content_kinds






# HTML --> TEXT CLEANING
################################################################################

def get_text(x):
    """
    Extract text contents of `x`, normalizing newlines to spaces and stripping.
    """
    return "" if x is None else x.get_text().replace('\r', '').replace('\n', ' ').strip()




# BASE CRAWLER
################################################################################

class BaseCrawler(object):
    """
    Basic web crawler that uses the breadth first search to visit all pages of a
    website starting from the `MAIN_SOURCE_DOMAIN` and browing pages recursively.
    Every page visited is aware of the `parent` (referring page), which makes it
    possible to consturct a web resource tree that can later be used to construct
    a ricecooker json tree, and ultimately a Kolibri channel.
    """
    # Base class proporties
    BASE_IGNORE_URLS = ['javascript:void(0)', '#']
    BASE_IGNORE_URL_PATTERNS = ['^mailto:.*', '^javascript:.*']
    GLOBAL_NAV_THRESHOLD = 0.7

    # Subclass constants
    MAIN_SOURCE_DOMAIN = None   # should be defined in subclass
    SOURCE_DOMAINS = None       # should be defined in subclass
    START_PAGE = None           # should be defined in subclass
    IGNORE_URLS = []            # should be defined by subclass
    IGNORE_URL_PATTERNS = []    # should be defined by subclass
    # GLOBAL_NAV_LINKS = []  # site navigation links like /about should also be ignored

    # CACHE LOGIC
    SESSION = requests.Session()
    CACHE = FileCache('.webcache')


    # keep track of what pages we should crawl next:
    queue = queue.Queue()
    # queue tasks are tuples (url, parent) where
    #  - url (str): which page should be visited
    #  - parent (dict): the web resources dict of the referring page

    # keep track of how many times a given URL is seen during crawl
    # first time a URL is seen will be automatically followed, but
    # subsequent occureces will record link existence but not recurse
    global_urls_seen_count = defaultdict(int)  # DB of all urls that have ever been seen
    #  { 'http://site.../fullpath?a=b#c': 3, ... }
    urls_visited = {}  # 'http://site.../fullpath?a=b#c' --> cached version of html content


    def __init__(self, main_source_domain=None, start_page=None):
        if main_source_domain:
            self.MAIN_SOURCE_DOMAIN = main_source_domain
            self.SOURCE_DOMAINS = [self.MAIN_SOURCE_DOMAIN]
            self.START_PAGE = self.MAIN_SOURCE_DOMAIN + '/'
        if start_page:
            self.START_PAGE = start_page

        forever_adapter= CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=self.CACHE)
        for source_domain in self.SOURCE_DOMAINS:
            self.SESSION.mount(source_domain, forever_adapter)   # TODO: change to less aggressive in final version


    # GENERIC URL HELPERS
    ############################################################################

    def path_to_url(self, path):
        """
        Returns url from path.
        """
        if path.startswith('/'):
            url = self.MAIN_SOURCE_DOMAIN + path
        else:
            url = path
        return url

    def url_to_path(self, url):
        """
        Removes MAIN_SOURCE_DOMAIN from url if startswith.
        """
        if url.startswith(self.MAIN_SOURCE_DOMAIN):
            path = url.replace(self.MAIN_SOURCE_DOMAIN, '')
        else:
            path = url
        return path


    def should_visit_url(self, url):
        """
        Returns True if `url` doesn' match any of the IGNORE criteria.
        """
        # 1. run through ignore lists
        if url in self.BASE_IGNORE_URLS or url in self.IGNORE_URLS:
            return False
        for pattern in self.BASE_IGNORE_URL_PATTERNS:
            match = re.match(pattern, url)
            if match:
                return False
        for pattern in self.IGNORE_URL_PATTERNS:
            match = re.match(pattern, url)
            if match:
                return False

        # 2. check if url is on one of the specified source domains
        found = False
        for source_domain in self.SOURCE_DOMAINS:
            if url.startswith(source_domain):
                found = True
        return found



    # CRAWLING TASK QUEUE API
    ############################################################################

    def enqueue_url(self, url, parent, force=False):
        if url not in self.global_urls_seen_count.keys() or force:
            # print('adding to queue:  url=', url)
            self.queue.put((url, parent))
        else:
            pass
            # print('Not craling url', url, 'beacause previously seen')
        self.global_urls_seen_count[url] += 1


    def enqueue_path(self, path, parent, force=False):
        full_url = self.path_to_url(path)
        self.enqueue_url(full_url, parent, force=force)



    # BASE PAGE HANDLER
    ############################################################################

    def on_page(self, url, page, parent):
        # print('Procesing page', url)
        page_dict = dict(
            kind='PageWebResource',
            url=url,
            parent=parent,
            children=[],
        )
        parent['children'].append(page_dict)

        links = page.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('href'):

                href = link['href']
                if href.startswith('/'):
                    url = self.MAIN_SOURCE_DOMAIN + href
                else:
                    url = href

                if self.should_visit_url(url):
                    # print(i, href)
                    self.enqueue_url(url, page_dict)
                    # parent['children'].append(url
                else:
                    page_dict['children'].append({
                        'url': url,
                        'kind': 'NoFollowLink',
                        'parent': page_dict,
                        'children': [],
                    })
            else:
                pass
                # print(i, 'nohref', link)



    # WEB RESOURCE MANIPULATIONS
    ############################################################################
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

        # top 10, sorted by count
        sorted_path_count_tuples = sorted(path_count_tuples, key=lambda t: t[1], reverse=True)
        print('top 10 paths', sorted_path_count_tuples[0:show_top])
        return sorted_path_count_tuples[0:show_top]



    def print_tree(self, tree_root, print_depth=3, hide_keys=[]):
        """
        Print contents of web resource tree starting at `tree_root`.
        """

        def _url_to_path_or_none(url):
            if url.startswith(self.MAIN_SOURCE_DOMAIN):
                path = url.replace(self.MAIN_SOURCE_DOMAIN, '')
                return path
            else:
                return None

        def print_web_resource_node(node, depth=0):
            INDENT_BY = 2

            extra_attrs = ''
            if 'kind' in node:
                extra_attrs = ' ('+node['kind']+') '

            if 'url' in node:
                path = _url_to_path_or_none(node['url'])
                if path:
                    print(' '*INDENT_BY*depth + '  -', 'path:', path, extra_attrs)
                else:
                    print(' '*INDENT_BY*depth + '  -', 'url:', node['url'], extra_attrs)
            elif 'path' in node:
                print(' '*INDENT_BY*depth + '  -', 'path:', node['path'], extra_attrs)

            if depth < print_depth:
                if len(node['children']) > 0:
                    print(' '*INDENT_BY*depth + '   ', 'children:')
                    for child in node['children']:
                        print_web_resource_node(child, depth=depth+1)
            else:
                    print(' '*INDENT_BY*depth + '   ', 'has', str(len(node['children'])), 'children')
        print_web_resource_node(tree_root)



    def infer_gloabal_nav(self, tree_root):
        """
        Returns a list of web resources that are likely to be global naviagin links
        like /about, /contact, etc.
        Adding the urls of these resources to
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
            Returns True if `url` is a global nav link.
            """
            seen_count = self.global_urls_seen_count[url]
            print('float(seen_count)/total_urls_seen_count', float(seen_count)/total_urls_seen_count, seen_count, total_urls_seen_count, self.url_to_path(url))

            # if previously determined
            for global_nav_resource in global_nav_nodes['children']:
                if url == global_nav_resource['url']:
                    return True
            # if new link that is seen a lot
            if float(seen_count)/total_urls_seen_count > self.GLOBAL_NAV_THRESHOLD:
                return True
            return False

        def recusive_visit1_rm_global_nav_children(subtree):
            newchildren = []
            for child in subtree['children']:
                # print(child)
                child_url = child['url']
                if len(child['children'])== 0 and _is_likely_global_nav(child_url):
                    print('Found global nav url =', child_url)
                    global_nav_resource = dict(
                        kind='GlobalNavLink',
                        url=child_url,
                    )
                    global_nav_resource.update(child)
                    global_nav_nodes['children'].append(global_nav_resource)
                else:
                    clean_child = recusive_visit1_rm_global_nav_children(child)
                    newchildren.append(clean_child)
            subtree['children'] = newchildren
            return subtree

        recusive_visit1_rm_global_nav_children(tree_root)
        return global_nav_nodes


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



    # MAIN LOOP
    ############################################################################

    def crawl(self, limit=1000):
        start_url = self.START_PAGE
        chennel_dict = dict(
            url='THIS IS THE TOP LEVEL CONTAINER FOR THE GRAWLER. ITS UNIQUE CHILD NODE IS THE ROOT.',
            title='Tahrir Academy Website',
            children=[],
        )
        self.enqueue_url(start_url, chennel_dict)

        counter = 0
        while not self.queue.empty():
            # print('queue.qsize()=', self.queue.qsize())
            url, parent = self.queue.get()
            page = self.download_page(url)
            self.urls_visited[url] = page  # cache BeatifulSoup parsed html in memory
            #
            # main handler dispatcher logic
            path = url.replace(self.MAIN_SOURCE_DOMAIN, '')
            handled = False
            # for pat, handler_fn in self.rules:
            #     if pat.match(path):
            #         handled = True
            #         handler_fn(url, page, parent)
            if not handled:
                self.on_page(url, page, parent)

            # limit crawling to 1000 pages by default (failsafe default)
            counter += 1
            if limit and counter > limit:
                break

        # cleanup remove parent links before output tree
        self.cleanup_web_resource_tree(chennel_dict)
        return chennel_dict

    def download_page(self, url):
        """
        Download url and soupify.
        """
        print('Downloading page with url', url)
        html = self.SESSION.get(url).content
        page = BeautifulSoup(html, 'html.parser')
        return page


# CLI
################################################################################

if __name__ == '__main__':
    crawler = BaseCrawler()
    channel_dict = crawler.crawl()

    with open('web_resource_tree.json', 'w') as wrt_file:
        json.dump(channel_dict, wrt_file, indent=2)
















