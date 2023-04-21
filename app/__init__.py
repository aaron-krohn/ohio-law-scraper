import cherrypy
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

from .scraper import OhioLegalScraper


class OhioLegalApp:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('app/templates'))

    @cherrypy.expose
    def index(self):

        raise cherrypy.HTTPRedirect('/ohio-constitution')

    @cherrypy.expose
    def ohio_constitution(self):

        path = 'ohio-constitution'
        cache = f'{path}.json'

        scraper = OhioLegalScraper(path=path, cache_file=cache)
        articles = scraper.scrape_data

        tmpl = self.env.get_template('index.j2')
        return tmpl.render({'year': datetime.now().strftime('%Y'), 'base_url': "https://codes.ohio.gov/", 'articles': articles})


    @cherrypy.expose
    def ohio_revised_code(self):

        path = 'ohio-revised-code'
        cache = '%s.json' % path

        scraper = OhioLegalScraper(path=path, cache_file=cache)
        articles = scraper.scrape_data

        tmpl = self.env.get_template('index.j2')
        return tmpl.render({'year': datetime.now().strftime('%Y'), 'base_url': "https://codes.ohio.gov/", 'articles': articles})


    @cherrypy.expose
    def ohio_administrative_code(self):

        path = 'ohio-administrative-code'
        cache = '%s.json' % path

        scraper = OhioLegalScraper(path=path, cache_file=cache)
        articles = scraper.scrape_data

        tmpl = self.env.get_template('index.j2')
        return tmpl.render({'year': datetime.now().strftime('%Y'), 'base_url': "https://codes.ohio.gov/", 'articles': articles})


    def error_page(status, message, traceback, version):
        return "Error (%s): %s" % (status, message)

