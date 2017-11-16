#!/usr/bin/env python
import os
import sys
from ricecooker.utils import data_writer, path_builder, downloader
from le_utils.constants import licenses, exercises, content_kinds, file_formats, format_presets, languages


from takehome_crawler import TakeHomeCrawler

# Additional imports
###########################################################
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Run Constants
###########################################################
CHANNEL_NAME = "CrawlerDemo_TakeHomeTest"              # Name of channel
CHANNEL_SOURCE_ID = "crawlerdemo_learningequality"      # Channel's unique id
CHANNEL_DOMAIN = "learningequality.org"                    # Who is providing the content
CHANNEL_LANGUAGE = "en"        # Language of channel
CHANNEL_DESCRIPTION = "sample channel used for the chef take home test."  # Description of the channel (optional)
CHANNEL_THUMBNAIL = None                                    # Local path or url to image file (optional)
PATH = path_builder.PathBuilder(channel_name=CHANNEL_NAME)  # Keeps track of path to write to csv
WRITE_TO_PATH = "{}{}{}.zip".format(os.path.dirname(os.path.realpath(__file__)), os.path.sep, CHANNEL_NAME) # Where to generate zip file



CRAWLING_STAGE_OUTPUT = TakeHomeCrawler.CRAWLING_STAGE_OUTPUT



# Additional Constants
###########################################################

BASE_URL = 'http://chef-take-home-test.learningequality.org/'

# only add keys we actively care about
METADATA_KEYS = ['content_id', 'author', 'lang_id', 'license', 'copyright_holder']
LICENSE_LOOKUP = {"CC BY-NC-SA": licenses.CC_BY_NC_SA,
                  "CC BY-NC": licenses.CC_BY_NC,
                  "CC BY": licenses.CC_BY,
                  "Public Domain": licenses.PUBLIC_DOMAIN
                  }

# Set up logging tools
LOGGER = logging.getLogger()
__logging_handler = logging.StreamHandler()
LOGGER.addHandler(__logging_handler)
LOGGER.setLevel(logging.INFO)

# License to be used for content under channel
CHANNEL_LICENSE = licenses.CC_BY

""" Main Scraping Method """
###########################################################
def scrape_source(writer):
    """ scrape_source: Scrapes channel page and writes to a DataWriter
        Args: writer (DataWriter): class that writes data to folder/spreadsheet structure
        Returns: None
    """
    handle_page_and_subpages(BASE_URL, "Sample Channel")  # Where does this "Sample Channel" string come from if "" is passed? I think it's from the website.


""" Helper Methods """
###########################################################

def read_source(url):
    """ Read page source as beautiful soup """
    html = downloader.read(url)
    return BeautifulSoup(html, 'html.parser')

def handle_page_and_subpages(url, parent_path):
    """Create CSV and ZIP for this URL and its descendants.
    parent_path is the name of the path in the ZIP file for this URL.
    Returns nothing."""

    metadata, content, children = handle_page(url)

    # should we only do this if we have children? Not sure...
    LOGGER.info("Adding folder {} ({})".format(parent_path, metadata['title']))
    if children:
        writer.add_folder(path = parent_path,
                          title = metadata['title'],
                          source_id = metadata.get('content_id'),
                          language = metadata.get('lang_id'),
                          description = metadata.get('description'),
                          )

    for content_item in content:
        writer.add_file(path = parent_path,
                        title = metadata['title'],
                        download_url = content_item,
                        author = metadata.get('author'),
                        source_id = metadata.get('content_id'),
                        description = metadata.get('description'),
                        language = metadata.get('lang_id'),
                        license=LICENSE_LOOKUP[metadata['license']],
                        copyright_holder = metadata['copyright_holder'])

    for child in children: # recurse
        LOGGER.debug("Processing {}".format(child['url']))
        child_path = '/'.join([parent_path.rstrip('/'),child['machine_name'].rstrip('/')])
        handle_page_and_subpages(child['url'], child_path)


def handle_page(url):
    """
    Takes a url and returns a list of three things:
        * metadata: a dictionary of strings (see METADATA_KEYS)
        * content: a list of URLs to content (e.g. video files)
        * children: a dictionary of the 'name' and fully-qualified 'url' of sub-resources, along with a short 'machine_name'

    Perhaps this should be three separate functions, instead.
    """
    def absolute_url(url_fragment):
        """Takes a URL fragment, and returns a full URL"""
        return urljoin(url, url_fragment)

    def no_brackets(text):
        """Gets rid of one set of bracketted text (like this)"""
        lbracket = text.index("(")
        rbracket = text.index(")")
        if lbracket == -1 or rbracket == -1: return text
        if lbracket > rbracket: return text
        return (text[:lbracket] + text[rbracket+1:]).rstrip()

    page = read_source(url)
    maincontent = page.find('div', {'class': 'maincontent'})

    children = []
    children_bs = maincontent.find_all('li', {'class': lambda x: x.endswith('-kind')})  # topic-kind, audio-kind, etc.
    for child in children_bs:
        child_url=child.find('a')['href']
        children.append({ "url": absolute_url(child_url),
                          "machine_name": child_url,
                          "name": no_brackets(child.get_text().strip()) })

    metadata = {}
    metadata_bs = maincontent.find('ul', {'class': 'metadata'})
    for key in METADATA_KEYS:
        item = metadata_bs.find("li", {'class': key})
        try:
            value = item.find("span", {'class': 'keyvalue'})
        except:
            LOGGER.debug("No {} found for {}".format(key, url))
            continue

        metadata[key] = value.get_text().strip()

    metadata['title'] = maincontent.find("h3").get_text().strip()
    metadata['description'] = maincontent.find("p", {'class': 'descr'}).get_text().strip()

    content = []
    tags_with_src = maincontent.find_all("", {'src': lambda x: x}) # there is a src tag
    for tag in tags_with_src:
        content.append(absolute_url(tag['src']))

    return (metadata, content, children)


""" This code will run when the sous chef is called from the command line. """
if __name__ == '__main__':

    # Open a writer to generate files
    with data_writer.DataWriter(write_to_path=WRITE_TO_PATH) as writer:

        # Write channel details to spreadsheet
        thumbnail = writer.add_file(str(PATH), "Channel Thumbnail", CHANNEL_THUMBNAIL, write_data=False)
        writer.add_channel(CHANNEL_NAME, CHANNEL_SOURCE_ID, CHANNEL_DOMAIN, CHANNEL_LANGUAGE, description=CHANNEL_DESCRIPTION, thumbnail=thumbnail)

        # Scrape source content
        scrape_source(writer)

        sys.stdout.write("\n\nDONE: Zip created at {}\n".format(writer.write_to_path))
