Data model
==========


LE Trees
--------
All tree data structures follow the same structure based on `children` attribute
which is list-like and contains the child nodes. Leaf nodes can be recognized by
their zero-length `children` attributes.

    {
      "key":"parentval",
      "children":[
         {"key": "childval1", "children":[]},
         {"key": "childval2", "children":[]}
      ]
    }

Additionally, while chef is running, nodes are annotated with `parent` attributes
that point to the parent node in the tree.




Crawling data model
-------------------
During the crawl web resources are represented objects with different attributes.
The `url` attribute will always be present.

1. When a URL is encountered, we add a "download request" to the crawling queue
   that is a tuple `(url, context)`, where `context` (dict) contains a link to
   the parent web resources (the referring page) and any optional extra metadata:

        {
          "parent": { dict of parent page },
          "somekey": "Some extra value passed from parent page to child page",
        }

2. During the crawl, the web resource is represented as a dictionary that
   can store arbitrary metadata. Web resources are organized into a tree based
   on the `children` attribute of nodes. A back-link to the parent nodes is also
   maintained. This is an example of a web resource that is a leaf node:

        {
          "kind": "LessonWebResource",
          "url": "http://site.org/path/lesson.html",
          "somekey": "Some extra value passed from parent page to child page",
          "title": "Title obtained during crawling",
          "parent": { dict of parent page (referrer) },
          "children": [],
        }

3. When the crawling is finished, the `cleanup_web_resource_tree` method is called
   in order to remove `parent` links:

        {
          "kind": "LessonWebResource",
          "url": "http://site.org/path/lesson.html",
          "somekey": "Some extra value passed from parent page to child page",
          "title": "Title obtained during crawling",
          "children": [],
        }

The output of of the crawling stage is the `chefdata/trees/web_resource_tree.json`.




Scraping output as SousChef Archive
-----------------------------------
See [souschef docs](https://github.com/learningequality/ricecooker/blob/master/docs/souschef.md).




Scraping output as Ricecooker Json Tree
---------------------------------------
It is not the resposibility of the crawler to extract the actual content from the
web resources it encounters. We'll do the detailed content and metadata extraction
during the scraping part of the pipeline.

During the scraping stage, a ricecooker chef script walks a web resource tree to
and retrieves and processes each of the web resources to extract all the metadata
needed to create an appropriate Kolibri Studio TopicNode or ContentNode.

For example, when the scraper encounters the web resource record:

    {
      "kind": "LessonWebResource",
      "url": "http://site.org/path/lesson.html",
      "somekey": "Some extra value passed from parent page to child page",
      "title": "Title obtained during crawling",
      "children": [],
    }

The scraper will:

  - download the URL (served from `.webcache` because previously retrieved)
  - process the HTML of the lesson to extract only the specific parts
    (remove header & global nav links which would not work offline)
  - download all the associated images, css, js, and other files for the lesson
  - create a zip file and save all these the above while rewriting all links to
    use relative hrefs like `href="./js/something.js"`.

The scraping stage output is stored in the file `chefdata/trees/ricecooker_json_tree.json`
and is in Ricecooker Json Tree format:


    {
      "kind": "html5",
      "source_id": "site:path/lesson.html",
      "title": "Title obtained during crawling",
      "description": "Detailed description obtained during scraping",
      "language": "en",
      "license": {
        "license_id": "CC BY",
        "description": null,
        "copyright_holder": "Site Organization Name"
      },
      "files": [
        {
          "file_type": "HTMLZipFile",
          "path": "/var/folders/k3/r74jr38d56v717n39fd073f80000gn/T/tmp1597010z.zip",
          "language": "en"
        }
      ],
      "thumbnail": null,
    }

This is the "native" format for Ricecooker API. Each record corresponds one-to-one
with the parameters needed to initialize an instance of one of the classes `ricecooker.nodes`
which will perform all subsequent metadata validation checks and upload the structure,
metadata, and content to Kolibri Studio.







