BasicCrawler
============

Semi-automated crawling bot with special features for extracting website structure automatically.

```
from basiccrawler.crawler import BasicCrawler

SOURCE_DOMAIN='http://learningequality.org'
start_page = 'http://learningequality.org/kolibri/'

class LECrawler(BasicCrawler):
    pass

crawler = LECrawler(main_source_domain=SOURCE_DOMAIN,
                    start_page=start_page)

web_resource_tree = crawler.crawl()
```

The crawler concludes will summary of the findings (according to crude heuristics).
```
# CRAWLER RECOMMENDATIONS BASED ON URLS ENCOUNTERED:
################################################################################
1. These URLs are very common and look like global navigation links:
  -  http://learningequality.org/about/team/
  -  http://learningequality.org/about/board/
  -  http://learningequality.org/about/supporters/
  -  ...
2. These are common path fragments found in URLs paths, so could correspond to site struture:
  -  ...
################################################################################
```


The web resource tree contains the information about the site structure at a high
level (`print_depth=3`) or in full detail (`print_depth=100`). For example:

```
crawler.print_tree(web_resource_tree, print_depth=4)

     - path: /kolibri/  (PageWebResource) 
       children:
        - path: /  (PageWebResource) 
          children:
           - path: /media/Rapport-Etude-Cameroun_KL_ENG.pdf  (MediaWebResource) 
        - path: /about/  (PageWebResource) 
          children:
           - path: /ka-lite/map/  (PageWebResource) 
        - path: /about/values/  (PageWebResource) 
        - path: /about/team/  (PageWebResource) 
        - path: /about/board/  (PageWebResource) 
        - path: /about/supporters/  (PageWebResource) 
        - path: /about/press/  (PageWebResource) 
        - path: /about/jobs/  (PageWebResource) 
        - path: /about/internships/  (PageWebResource) 
          children:
           - path: https://learningequality.org/about/jobs/?gh_jid=533166  (PageWebResource) 
        - path: /download/  (PageWebResource) 
        - path: /documentation/  (PageWebResource) 
        - path: /hardware_grant/  (PageWebResource) 
        - path: /ka-lite/  (PageWebResource) 
          children:
           - path: /ka-lite/infographic/  (PageWebResource) 
        - path: /translate/  (PageWebResource) 
        - path: https://blog.learningequality.org/?gi=2589e076ea04  (PageWebResource) 
        - path: /ka-lite/map/add/  (PageWebResource) 
        - path: /donate/  (PageWebResource) 
          children:
           - path: /static/doc/learning_equality_irs_determination_letter.pdf  (MediaWebResource) 
        - path: /cdn-cgi/l/email-protection  (PageWebResource) 
```

For this crawl, we didn't find too many educational materials (docs/videos/audio/webapps),
but at least we get some idea of the links on that page. Try it on another website.




Example usage
-------------
https://github.com/learningequality/sushi-chef-tessa/blob/master/tessa_cralwer.py#L229



TODO
----
  - Update examples + notebooks
  - path to url / vice versa (and possibly elsewhere): consider `urllib.urlparse`?
    [e.g. `url.startwith(source_domain)` could be `source_domain in url.domain`
    to make it more flexible with subdomains
    - Additional valid domains can be specified but `url_to_path_list` assumes adding CHANNEL_ROOT_DOMAIN
   	  [we may wish to expand all links based on parent URL]
    - refactor and remove need for MAIN_SOURCE_DOMAIN and use only SOURCE_DOMAINS instead


Future feature ideas
--------------------
  - Asynchronous download (not necessary but might be good for performance on large sites)
    - don't block for HTTP
    - allow multiple workers getting from queue
  - content_selector hints for default `on_page` handler to follow links only within
    a certain subset of the HTML tree. Can have:
     - site-wide selector at class level
     - pass in additional `content_selector` from referring page via context dict
  - Automatically detect standard embed tags (audio, video, pdfs) and add links to
    web resource tree in default `on_page` handler.



Crawler API
-----------
The goal of the `BasicCrawler` class is to help with the initial exploration of
the source website. It is your responsibility to write a subclass that uses the HTML,
URL structure, and content to guide the crawling and produce the web resource tree.

Your crawler should inherit from `BasicCrawler` and define:

1. What site we're crawling and where to start:
   - set the following attributes
     - `MAIN_SOURCE_DOMAIN` e.g. `'https://learningequality.org'`
       or pass as arg `main_source_domain` at creation time.
     - `START_PAGE` e.g. `'https://learningequality.org/'`
       or pass at creation time as `start_page`.
    - `IGNORE_URLS=[]`: crawler will ignore these URLs (can be specified as str, re, or callable)
    - `CRAWLING_STAGE_OUTPUT='chefdata/trees/web_resource_tree.json'`: where the
      output of the crawling will be stored

2. Run for the first time by calling `crawler.crawl()` or as a command line script
  - The BasicCrawler has logic for visiting pages and will print out on the
    a summary of the auto inferred site stricture findings and recommendations
    based on the URL structure observed during the initial crawl.
  - Based on the number of times a link appears on different pages of the site
    the crawler will suggest to you candidates for global navigation links.
    Most websites have an /about page, /contact us,  and other such non-content-containing pages,
    which we do not want to include in the web resource tree.
    You should inspect these suggestions and decide which should be ignored
    (i.e. not crawled or included in the web_resource_tree output).
    To ignore URLs you can edit the attributes:
      - `IGNORE_URLS`: crawler will ignore these URLs
    Edit your crawler subclass' code and append to `IGNORE_URLS`
    the URLs you want to skip (anything that is not likely to contain content).

3. Run the crawler again, this time there should be less noise in the output.
  - Note the suggestion for different paths that you might want to handle specially
    (e.g. `/course`, `/lesson`, `/content`, etc.)
    You can define class methods to handle each of these URL types:

         def on_course(self, url, page, context):
             # what do you want the crawler to do when it visits the  course with `url`
             # in the `context` (used for extra metadata; contains reference to parent)
             # The BeautifulSoup parsed contents of the `url` are provided as `page`.

         def on_lesson(self, url, page, context):
             # what do you want the crawler to do when it visits the lesson

         def on_content(self, url, page, context):
             # what do you want the crawler to do when it visits the content url


Check out the default `on_page` method so see how a web resource tree is constructed:
https://github.com/learningequality/BasicCrawler/blob/master/basiccrawler/crawler.py#L212
    
    
    

