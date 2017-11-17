#!/usr/bin/env python
import json
import os
import sys
from ricecooker.utils import data_writer, path_builder, downloader
from le_utils.constants import licenses, content_kinds, file_formats, format_presets, languages


from takehome_crawler import TakeHomeCrawler

# Additional imports
###########################################################
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

# only add keys we actively care about
METADATA_KEYS = ['content_id', 'author', 'lang_id', 'license', 'copyright_holder']
LICENSE_LOOKUP = {
    "CC BY-NC-SA": licenses.CC_BY_NC_SA,
    "CC BY-NC": licenses.CC_BY_NC,
    "CC BY": licenses.CC_BY,
    "Public Domain": licenses.PUBLIC_DOMAIN
}

# Set up logging tools
LOGGER = logging.getLogger()
__logging_handler = logging.StreamHandler()
LOGGER.addHandler(__logging_handler)
LOGGER.setLevel(logging.INFO)



# Main Scraping Method
###########################################################
def scrape_source(writer):
    """ scrape_source: Scrapes channel page and writes to a DataWriter
        Args: writer (DataWriter): class that writes data to folder/spreadsheet structure
        Returns: None
    """
    web_resource_tree = json.load(open(CRAWLING_STAGE_OUTPUT,'r'))
    recusive_scrape_web_resouce(web_resource_tree)


# Web resource tree walking logic
################################################################################

CHANNEL_ROOT_DOMAIN = "http://chef-take-home-test.learningequality.org"

def url_to_path_list(url):
    """
    Extracts the path of the current location within channel folder in zip file
    from the url provided.
      - If channel or topic node path is  CHANNEL_NAME+'/'.join(path_list)
      - If content node path is  CHANNEL_NAME+'/'.join(path_list[0:-1])
    """
    path = url.replace(CHANNEL_ROOT_DOMAIN, '')
    path_list = path.split('/')[0:-1]
    return path_list

def recusive_scrape_web_resouce(subtree):
    """
    Create CSV and ZIP by scraping this web resouce node and its descendants.
    `CHANNEL_NAME` is the name of the path in the ZIP file for this subtree.
    Returns nothing.
    """
    url = subtree['url']
    path_list = url_to_path_list(url)
    metadata, content = scrape_page(url)
    # channel and topics have metadata only and content==None
    # content nodes like document/audio/video have metadata and content (file URL)

    kind = subtree['kind']
    # dispatch based on node kind ##############################################
    if kind == 'channel':
        channel_path = CHANNEL_NAME
        writer.add_folder(
                path = channel_path,
                title = metadata['title'],
                source_id = metadata.get('content_id'),
                language = metadata.get('lang_id'),
                description = metadata.get('description'),
        )
        LOGGER.info("Added channel root folder {}".format(metadata['title']))

    elif kind == 'topic':
        parent_path = CHANNEL_NAME + '/'.join(path_list)
        writer.add_folder(
                path = parent_path,
                title = metadata['title'],
                source_id = metadata.get('content_id'),
                language = metadata.get('lang_id'),
                description = metadata.get('description'),
        )
        LOGGER.debug("Added folder {}/{}".format(parent_path, metadata['title']))

    elif kind in ['document', 'audio', 'video']:
        parent_path = CHANNEL_NAME + '/'.join(path_list[0:-1])
        writer.add_file(
                path = parent_path,
                title = metadata['title'],
                download_url = content,
                author = metadata.get('author'),
                source_id = metadata.get('content_id'),
                description = metadata.get('description'),
                language = metadata.get('lang_id'),
                license=LICENSE_LOOKUP[metadata['license']],
                copyright_holder = metadata['copyright_holder'])
        LOGGER.debug("Added content {}/{}".format(parent_path, metadata['title'])+str(content))

    # recurse
    for child in subtree['children']:
        child_url = child['url']
        LOGGER.debug("Recusing in child {}".format(child_url))
        recusive_scrape_web_resouce(child)


def scrape_page(url):
    """
    Takes a url and returns:
        * metadata: a dictionary of strings (see METADATA_KEYS)
        * content: a list of URLs to content (e.g. video files)
    """
    page = read_source(url)
    metadata = scrape_metadata(page)
    content = scrape_content(url, page)
    return (metadata, content)


def scrape_metadata(page):
    """
    Extract all available metadata for a given topic node or content node.
    """
    maincontent = page.find('div', {'class': 'maincontent'})
    metadata = {}
    metadata_bs = maincontent.find('ul', {'class': 'metadata'})
    for key in METADATA_KEYS:
        item = metadata_bs.find("li", {'class': key})
        try:
            value = item.find("span", {'class': 'keyvalue'})
        except:
            LOGGER.debug("Key {} not found.".format(key))
            continue
        metadata[key] = value.get_text().strip()

    metadata['title'] = maincontent.find("h3").get_text().strip()
    metadata['description'] = maincontent.find("p", {'class': 'descr'}).get_text().strip()
    return metadata


def scrape_content(url, page):
    """
    Generic scraper for audio/video/pdf based on src atteibute.
    """
    def _absolute_url(url_fragment):
        """
        Interprets a URL fragment relative to current URL and returns a full URL.
        """
        return urljoin(url, url_fragment)

    maincontent = page.find('div', {'class': 'maincontent'})
    tags_with_src = maincontent.find("", {'src': lambda x: x}) # there is a src tag
    if tags_with_src:
        content = _absolute_url(tags_with_src['src'])
        return content
    else:
        return None


def read_source(url):
    """
    Read page source as beautiful soup.
    """
    html = downloader.read(url)
    return BeautifulSoup(html, 'html.parser')



# This code will run when the sous chef is called from the command line.
################################################################################
if __name__ == '__main__':

    # Open a writer to generate files
    with data_writer.DataWriter(write_to_path=WRITE_TO_PATH) as writer:

        # Write channel details to spreadsheet
        thumbnail = writer.add_file(str(PATH), "Channel Thumbnail", CHANNEL_THUMBNAIL, write_data=False)
        writer.add_channel(CHANNEL_NAME, CHANNEL_SOURCE_ID, CHANNEL_DOMAIN, CHANNEL_LANGUAGE, description=CHANNEL_DESCRIPTION, thumbnail=thumbnail)

        # Scrape source content
        scrape_source(writer)

        sys.stdout.write("DONE: Zip created at {}\n".format(writer.write_to_path))
