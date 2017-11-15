
We can partition the chef pipeline in such a way that we can monitor each stage and have visibility into the steps of the transformation.

This sushi chef will function as a three-step process:

crawl
scrape
create channel

Crawl stage
-----------

In the first step we'll just crawl the website to build a hierarchy of folders and lessons. The output of this step is a JSON file of lesson urls to be retrieved. The tree corresponds to the results of the crawl, by languages, by topic, and by topic cluster (if applicable):





Channel

Third stage will build the actual ricecooker tree with the objects according to the classes specified in the JSON and upload it to Content Workshop.






The schema for the data in `ricecooker_tree.json` follows the `ricecooker` API
and contains the metadata needed to upload a content channel to Kolibri Studio.

Note: The intermediate representation `web_resource_tree.json` is optional, and
it is possible to create the `ricecooker_tree.json` by other means,
or to use the `ricecooker` API directly (best approach for Python experts).





