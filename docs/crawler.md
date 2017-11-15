
Generic crawler design
======================

The class `BasicCrawler` implements basic web crawling logic that content
developers can use to make their life easier when crawling educational sites.


    website --crawl--> web_resource_tree.json --scrape--> ricecooker_tree.json --uploadchannel--> Studio

The data in the `web_resource_tree.json` is an arbitrary schema that the chef
author comes up with while preparing the chef script. Usually the web resource
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


