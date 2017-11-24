Generic crawler design
======================
The class `BasicCrawler` implements basic web crawling logic that content
developers can use to make their life easier when crawling educational sites.

Normal ricecooker flow:

    website --crawl--> web_resource_tree.json --scrape--> ricecooker_tree.json --uploadchannel--> Studio


Souschef-LineCook flow:

    website --crawl--> web_resource_tree.json --scrape--> ChannelArchive.zip  --LineCook.uploadchannel--> Studio

The data in the `web_resource_tree.json` is an arbitrary schema that the chef
author comes up with while preparing the chef script. Usually the web resource
tree matches the source website structure:

    /course21                    {"kind":"course", "url":"http://site.org/course21.html", children=[
        /unitA                      {"kind":"unit", "url":"http://site.org/unitA.html", children=[]},
        /unitB                      {"kind":"unit", "url":"http://site.org/unitB.html", children=[
            /lesson        <--->        {"kind":"lesson", "url":"http://site.org/unitB/lesson.html", children=[
                /document                   {"kind":"document", "url":"http://site.org/document.pdf", children=[]},
                /video                      {"kind":"video", "url":"http://site.org/video.mp4", children=[]},
                /audio                      {"kind":"audio", "url":"http://site.org/recording.mp3", children=[]}


The purpose of building the `web_resource_tree.json` is to decide the hierarchical
structure of the future Kolibri Studio channel (`channel->topic->subtopic*-content`
structure expressed as a hierarchy of `TopicNode`s and `ContentNode`s).
The purpose of the `crawl` step is to build the mapping between the sites's structure
and the channel structure. Each node in the `web_resource_tree.json` tree has a `url`
and corresponds to some page from the site (main page, category page, course page, etc.).

Web resource nodes can have additional attributes like `title` and `description`,
but we're not concerned about extracting the full content of the site yet, which
we'll do in the scraping step.



Link following logic
--------------------
The default behaviour of the crawler is to follow links it finds on the pages.
There are three types of special scenarios this override this default behaviour:
  - 1. Ignore rules
  - 2. Media files
  - 3. Broken links

1. The crawler will ignore the link if it matches one of the IGNORE_URLS conditions.
Links for which `should_ignore_url` return True will not be examined any further.

2. Next we check for links that correspond to media files, which we want to make note of
in the web resource tree but not necessarily download during the crawling stage.
The function `is_media_file` performs file-extension-in-path and mime-type in HEAD
guessing strategies to determine if a given URL corresponds to a media file:

    verdict, response  =  is_media_file(url)

Where `response` is the HTTP response to a `requests.HEAD` for the URL
and `verdict` (bool) tells you if it's a media file.
When using `is_media_file` in your own handler functions you can use the response
headers to specific actions for this `url` based on:
  - `response.headers.get('Content-Type', None)`
  - `response.headers.get('Content-Disposition', None)` (see [this](https://pypi.python.org/pypi/rfc6266) for parsing)
  - `response.headers.get('Content-Length', None)`
The default `on_page` handler creates a `MediaWebResource`-kind dictionary from the
response headers for each media file and adds them as children to the current page.

3. The case when `response` is `None` for the `is_media_file` method call corresponds
   to broken links or other HTTP problem and should be handled before case 2.






The content pipeline
--------------------
We can partition the chef pipeline in such a way that we can monitor each stage
and have visibility into the steps of the transformation.

This sushi chef will function as a three-step process:
  - crawl (mostly a href selectors)
  - scrape (div/span/h2/img/css/PDF
  - create channel:
     - either use ricecooker framework to talk to HTTP uploads API on Kolibri Studio
     - or create local zip archive ready for `LineCook`


### Crawl part
In the first step we'll just crawl the website to build a topic-subtopic hierarchy
from the website's structure. The output of this step is a JSON file of web resource
urls that will be retrieved in the next step.

### Scraping part
The purpose of the `scrape` part of the pipeline is to extract all the content
from the source website, specifically titles, descriptions, authors, licenses,
for PDF documents, videos, mp3 files, HTML5 content, and exercises.

### Channel part
The third step is to build the actual ricecooker tree with the objects according
to the classes specified in the JSON and upload it to Content Workshop.
The schema for the data in `ricecooker_tree.json` follows the `ricecooker` API
and contains the metadata needed to upload a content channel to Kolibri Studio.

Note: The intermediate representation `web_resource_tree.json` is optional, and
it is possible to create the `ricecooker_tree.json` by other means,
or to use the `ricecooker` API directly (best approach for Python experts).

