# BasicCrawler
Basic web crawler that automates website exploration and producing web resource trees.











Usage
-----
The goal of the `BasicCrawler` class is to help with the initial exploration of
the source website. It is your responsibility to write a subclass that uses the HTML,
URL structure, and content to guide the crawling and produce the web resource tree.

The workflow is as follows

1. Create your subclass
   - set the following attributes
     - `MAIN_SOURCE_DOMAIN` e.g. `'https://learningequality.org'`
     - `START_PAGE` e.g. `'https://learningequality.org/'`

2. Run for the first time by calling `crawler.crawl()` or as a command line script
  - The BasicCrawler has basic logic for visiting pages and will print out on the
    a summary of the auto inferred site stricture findings and recommendations
    based on the URL structure observed during the initial crawl.
  - Based on the number of times a link appears on different pages of the site
    the crawler will suggest to you candidates for global navigation links.
    Most websites have an /about page, /contact us,  and other such non-content-containing pages,
    which we do not want to include in the web resource tree.
    You should inspect these suggestions and decide which should be ignored
    (i.e. not crawled or included in the web_resource_tree output).
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



