
RICECOOKER IDEA: BasicCrawler reusable class with basic crawling logic

Starting from a web page we would like to extract it structure in the form of a hierarchical tree. This is essentially what a site map would be but we want to generated for any site. to use case is to automatically build trees of web resource nodes that the later scraping stage can rearrange manipulate and most importantly extract the content from.


 consider a website crawl  that starts from the root page which contains links to 3 categories

pon visiting the root page the crawler sees the Three Links and queues them up for crawling later

in the next iteration the first link on the root page is next is up is popped from the cute and then we get all the links on that page and Sons on recursive.

Each task on the crawling task queue Is it to purple (url, parent)  where parent is the dictionary object the describes the referring page web resource.

 okay so what do we do with backlinks In order to build a tree from a graph we must disallow back links

 we will deal with files that appear in multiple places by duplication

 we will also allow side links

