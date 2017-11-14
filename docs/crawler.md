
Generic crawler design
======================

The class `BaseCrawler` implements basic web crawling logic that content
developers can use make their life easier when crawling educational sites.


    website --crawl--> web_resource_tree.json --scrape--> ricecooker_tree.json --uploadchannel--> Studio

The data in the `web_resource_tree.json` is an arbitrary schema that the chef
author comes up with while prepating the chef script. Usually the web resource
tree matches the source website structure:

        /course21
            /unit1
            /unit2
                /lesson                 <--->       TODO: add json hierarch of stuff on left
                    /document
                    /video
                    /exercises

The purpose of building the `web_resource_tree.json` is to decide the hierarchical
structure of the future Kolibri Studio channel (`channel->topic->subtopic*-content`
structure expressed as a hierarchy of `TopicNode`s and `ContentNode`s).
The purpose of the `crawl` step is to build the mapping between the sites's structure
and the channel structure. Each node in the `web_resource_tree.json` tree has a `url`
and corresponds to some page from the site (main page, category page, course page, etc.).

Web resource nodes can have additional attributes like `title` and `description`,
but we're not concerned about extracting the full content of the site yet, which
we'll do in the scraping step.

The purpose of the `scrape` step is to extract all the useful content from the
source website, specifically titles, descriptions, authors, licenses, for
PDF documents, videos, mp3 files, HTML5 content, and exercises.
The schema for the data in `ricecooker_tree.json` follows the `ricecooker` API
and contains the metadata needed to upload a content channel to Kolibri Studio.

Note: The intermediate representation `web_resource_tree.json` is optional, and
it is possible to create the `ricecooker_tree.json` by other means,
or to use the `ricecooker` API directly (best approach for Python experts).







Usage
-----
The goal of the `BaseCrawler` class is to help with the initial exploration of
the source website. It is your responsibility to write a subclass that uses the HTML,
URL structure, and content to guide the crawling and produce the web resource tree.

The workflow is as follows

1. Create your subclass
   - set the following attributes
     - `MAIN_SOURCE_DOMAIN` e.g. `'https://learningequality.org'`
     - `START_PAGE` e.g. `'https://learningequality.org/'`

2. Run for the first time by calling `crawler.crawl()` or as a command line script
  - The BaseCrawler has basic logic for visiting pages and will print out on the
    a summary of the auto inferred site stricture findings and recommendations
    based on the URL structure observed during the initial crawl.
  - Based on the number of times a link appears on different pages of the site
    the crawler will suggest to you candidates for global navigation links.
    Most websites have an /about page, /contact us,  and other such non-content-containing pages,
    which we do not want to include in the web resource tree.
    You you can inspect these suggestions and decide which should be ignored
    (i.e. not crawled or included in web_resource_tree).
    To ignore URLs you can edit the attributes:
      - `IGNORE_URLS` (list of strings): crawler will ignore this URL
      - `IGNORE_URL_PATTERNS` (list of RE objects): regular expression that do the same thing
    Edit your crawler subclass' code and append to `IGNORE_URLS` and `IGNORE_URL_PATTERNS`
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



Crawling data model
-------------------

During the crawl web resources url and are represented objects with different
attributes. The `url` attribute will always be present.

1. When a URL is encountered, we add a "download request" to the crawling queue
   that is a tuple `(url, context)`, where `context` (dict) contains a link to
   the parent web resources (the referring page) and any optional extra metadata:

        {
          "parent": { dict of parent page },
          "somekey": "Some extra value passed from parent page to child page",
        }

2. During the crawl, the web resource is represented as a dictionary will which
   can store arbitrary metadata. Web resources are organized into a tree based
   on the `children` attribute of nodes. A back-link to the parent nodes is also
   maintained. This is an example of a web resource that is a leaf node:

        {
          "kind": "FileWebResource",
          "url": "http://site.org/path/file.html",
          "somekey": "Some extra value passed from parent page to child page",
          "title": "Title obtained during crawling",
          "parent": { dict of parent page },
          "children": [],
        }

3. When the crawling is finished, the `cleanup_web_resource_tree` method is called
   in order to remove `parent` links:

        {
          "kind": "FileWebResource",
          "url": "http://site.org/path/file.html",
          "somekey": "Some extra value passed from parent page to child page",
          "title": "Title obtained during crawling",
          "children": [],
        }



Scraping
--------

3. After finishing the scraping part of the chef, the web resource is transformed
to ricecooker_json_tree format:

        {
          "kind": "html5",
          "url": "http://site.org/path/file.html",
          "title": "Title obtained during crawling",
          "description":
          "language":
        }
