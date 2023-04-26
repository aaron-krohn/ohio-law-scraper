import time
import json
import logging
import urllib.request

from bs4 import BeautifulSoup as bs


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class OhioLegalScraper:
    """Scrapes one of the three documents available on the Ohio Codes website:

        - https://codes.ohio.gov/ohio-constitution
        - https://codes.ohio.gov/ohio-revised-code
        - https://codes.ohio.gov/ohio-administrative-code

    The same code is used to scrape all three documents, despite minor differences in content and implementation.

    Earliest version was made using stdlib HTMLParser, but it quickly got out of hand.
    """

    def __init__(self, base_url='https://codes.ohio.gov/', path='ohio-constitution', delay=2, cache_file='ohio_constitution.json'):
        """Initializes the scraper. Defaults to scraping the shortest document, the Constituion.

        Automatically loads the cache file on init.
        See also: the `dedupe` argument for `OhioLegalScraper.scrape()`.

        Args:
            base_url: the base URL of the website to scrape, defaults to https://codes.ohio.gov/
            path: one of three available document paths: ohio-constitution, ohio-revised-code, ohio-administrative-code
            delay: The number of seconds to wait between page requests.
            cache_file: the json file written to during scraping
        """

        self.base_url = base_url
        self.path = path
        self.page_delay = delay
        self.cache_file = cache_file

        self.scrape_data = {'name': path, 'data': {}}
        self.scrape_data['url'] = '%s%s' % (self.base_url, self.path)

        self.load_cache(self.cache_file)

        self.cursor = TreeSeeker(self.scrape_data)


    def paginate(self, page, per_page=100, path=[]):
        # Goal: Walk the data, keeping the path. When page n >= first record and n <= last record, copy path and data

        out = {}

        dpointer = self.scrape_data
        for branch in path:
            dpointer = dpointer[branch]

        if 'data' in dpointer:

            for sname, sdata in dpointer['data']:
                new_path = path.append(sname)


    def scrape(self, tree_path=[], dedupe=True):
        """Recursively descends table of contents pages until hitting a law page.

        Writes the cache_file after every successful page scrape.

        Args:
            tree_path: list of keys used to address the current node for scraping
            dedupe: Set to `True` to prevent web requests for URLs with existing data.

        Returns:
            dict: the results of the scrape, a reference to self.scrape_data
        """

        dpointer = self.scrape_data
        for branch in tree_path:
            dpointer = dpointer['data'][branch]

        # Use existing data to prevent duplicate web requests
        # If the contents of the `dpointer` 'data' key isn't empty, and
        # deduplication is enabled with `True`, then don't scrape this page
        if dpointer.setdefault('data', {}) and dedupe is True:
            return

        logging.info('Scraping: %s', dpointer['url'])
        try:
            raw_html = self.html_request(dpointer['url'])
        except Exception as exc:
            logging.exception('Failed loading URL: %s', exc)
            logging.debug('DATA: %s', dpointer)
            return

        # There is a varying number of table of contents sub-tables,
        # depending on which document you're scraping. The easiest solution
        # to this was to handle it recursively and stop at the leaf nodes.
        if self.detect_toc(raw_html):
            page_data = self.parse_toc(raw_html)

            for name, data in page_data.items():
                time.sleep(self.page_delay)

                new_path = tree_path[:]
                new_path.append(name)

                dpointer['data'] = page_data

                self.scrape(tree_path=new_path, dedupe=dedupe)
                self.write_cache()

        else:
            page_data = self.parse_page(raw_html)
            dpointer['data'] = page_data
            self.write_cache()

        return self.scrape_data


    def html_request(self, url):
        """Uses built-in web request to fetch a page

        Args:
            url: the URL containing the desired HTML document

        Returns:
            string: a decoded string of the HTML document
        """
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')

        return html


    def detect_toc(self, raw_html):
        """Detects a table of contents page by checking for table.laws-table in the given document

        Args:
            raw_html: Raw html, not a BS4 instance

        Returns:
            boolean: True if a table of contents is found
        """

        b = bs(raw_html, 'html.parser')
        table = b.find('table', class_='laws-table')

        if table is None:
            return False

        return True


    def parse_toc(self, raw_html):
        """Parses a table of contents page, in the following structure:
             {"Article I": {
               "url": "https://codes.ohio.gov/ohio-constitution/article-1",
               "title": "Bill of Rights",
               "data": {
                 "Section 1": {
                   ...
                 },
               }
             }

        Args:
            raw_html: raw HTML, not a BS4 object
        Returns:
            dict: a data structure containing the scraped values
        """
        toc = {}

        b = bs(raw_html, 'html.parser')
        table = b.find('table', class_='laws-table')

        for link in table.find_all('a'):

            if 'class' in link.attrs or 'target' in link.attrs:
                continue

            link_name = link.text.strip()

            s = link.find('span')
            if s is not None:
                link_name = link.text.split(s.text)[0].strip()
                link_title = s.next_sibling.strip()

            link_name = link_name.split(',')[-1].strip()
            link_ref = link['href'].replace(self.path, '').strip('/')

            toc.setdefault(link_name, {})
            toc[link_name]['url'] = '%s%s/%s' % (self.base_url, self.path, link_ref)

            if s is not None:
                toc[link_name]['title'] = link_title

        return toc


    def parse_page(self, raw_html):
        """Scrapes a leaf node page into the following structure:
          {
           "Section 1": {
           "url": "https://codes.ohio.gov/ohio-constitution/section-1.1",
           "title": "Inalienable Rights",
           "data": {
             "effective": "1851",
             "text": "All men are, by nature, free and independent, and have certain inalienable rights, among which are those of enjoying and defending life and liberty, acquiring, possessing, and protecting    property, and seeking and obtaining happiness and safety."
             }
            }
          }

        Args:
            raw_html: raw HTML, not a BS4 object
        Returns:
            dict: a data structure containing the scraped values
        """

        sect = {}

        b = bs(raw_html, 'html.parser')

        s_text = b.find(class_='laws-body')
        if s_text is None:
            return sect

        eff = b.find('div', class_='laws-section-info-module')
        if eff:
            eff = eff.find('div', class_='value').text.strip()

        sect['effective'] = eff

        s_par = s_text.find_all('p')

        if s_par is not None:
            for idx, pg in enumerate(s_par):
                sect.setdefault('ps', [])
                out = {'order': idx}

                text = pg.text.strip()
                out['text'] = text

                classes = pg.get('class')
                if classes:
                    tab_depth = [x for x in classes if x.startswith('level-')].pop()
                    if tab_depth:
                        out['tabs'] = int(tab_depth[-1]) - 1

                sect['ps'].append(out)

        else:
            s_span = s_text.find('span')
            if s_span is not None:
                sect['ps'] = ({'order': 0, 'text': s_span.text.strip()},)

        return sect


    def load_cache(self, cache_file=None):
        """Loads cached data into the object.

        Args:
            cache_file: the JSON file to be loaded.
        """

        if cache_file is None:
            cache_file = self.cache_file

        try:
            with open(cache_file, 'r') as f:
                cache = json.loads(f.read())
            self.scrape_data = cache
        except FileNotFoundError as exc:
            logging.info('Cache file not found, skipping: %s', cache_file)


    def write_cache(self, cache_file=None):
        """Writes data into a JSON cache file.

        Args:
            cache_file: the JSON file to be written.
        """

        if cache_file is None:
            cache_file = self.cache_file

        try:
            with open(cache_file, 'w') as f:
                f.write(json.dumps(self.scrape_data))
        except Exception as exc:
            logging.exception('Failed writing cache: %s', exc)
            raise exc




if __name__ == '__main__':

    scraper = OhioLegalScraper()
    scraper.scrape()

