from .crawler imprt BasicCrawler



# TAHRIR ACADEMY CRAWLER
################################################################################

class TahrirAcademyCrawler(BasicCrawler):
    """
    This class implements page handler specific to the Tahrir Academy website.
    """
    # track youtube videos crawled in order to build the 'Miscellaneous' topic
    youtube_ids_from_site = []


    def __init__(self):
        self.rules = [
            (re.compile('^/$'), self.on_root),
            (re.compile('^/category/'), self.on_category),
        #     (re.compile('^/course/'), on_course),
        #     (re.compile('^/content/'), on_content),
        ]


    # PAGE HANDLERS
    ############################################################################

    def on_root(self, url, page, chennel_dict):
        print('Procesing root page', url)
        links = page.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('href'):
                print(i, link['href'])
            else:
                print(i, 'nohref', link)
        # extract categories for each track
        tracks_menu_div = page.find('div', id="subjects-menu")
        track_uls = tracks_menu_div.find_all('ul', recusive=False)
        for track_ul in track_uls:
            track_id = track_ul['id']
            track_dict = dict(
                kind=content_kinds.TOPIC,
                source_id='tahriracademy:'+track_id,
                title='Track ' + str(track_id),
                description='',
                children=[],
            )
            chennel_dict['children'].append(track_dict)
            track_categories = track_ul.find_all('li', recusive=False)
            for category_li in track_categories:
                category_link = category_li.find('a')
                category_path = category_link['href']
                self.enqueue_path(category_path, track_dict)


    def on_category(self, url, page, parent):
        print('Processing category', url)
        match = re.match('.*/category/(?P<id>\d+).*', url)
        category_id = match.groupdict()['id']
        category_dict = dict(
            kind=content_kinds.TOPIC,
            title='Category ' + str(category_id),
            description='',
            children=[],
        )
        parent['children'].append(category_dict)
        # scrape courses
        links = page.find_all('a')
        for i, link in enumerate(links):
            if link.has_attr('data-course-id'):
                data_course_id = link['data-course-id'] # e.g "49"
                # data_remote = link['data-remote'] # e.g. "/course/show-info/49?isInCourse=0"
                course_path = '/course/' + str(data_course_id)
                # self.enqueue_path(course_path, category_dict)
                category_dict['children'].append({'url':course_path})
            elif link.has_attr('href'):
                print('     ', i, link['href'])
            else:
                print(i, 'nohref', link)



    def on_course(self, url, page, parent):
        """
        This function is called when a URL matchin the "course rule"  is encountered.
        Parameters is `url` of page and parsed BeautifuSoup tree in `page`.
        The crawling page retrieval queue is accesible at `self.queue`.
        """
        print('Processing course', url)

        # get title
        title_h2 = page.find('h2', class_="course-title")     #  id="myModalLabel">
        title = get_text(title_h2)

        # get description
        desc = get_text(page.find('div', class_='course-desc'))
        print('desc=', desc)

        nav = page.find('nav', class_="course-content-menu")  # id="course-content-menu">
        nav_ul = nav.find('ul', class_="nav-pills")
        content_lis = nav_ul.find_all('li')
        for content_li in content_lis:
            content_id = content_li['id']
            content_link = content_li.find('a')
            content_path = '/content/' + str(content_id)
            self.enqueue_path(content_path)


    def on_content(self, url, page, parent):
        print('Processing content', url)
        iframe = page.find('iframe', id="youtubePlayer")
        if iframe:
            src = iframe['src']
            m = re.match('.*embed/(.*)\?.*', src)
            youtube_id = m[1]
            print('                   youtube_id found', youtube_id)
            self.youtube_ids_from_site.append(youtube_id)
        else:
            print('ZZZ did not find iframe for', url)

