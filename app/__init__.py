import cherrypy
import os

from jinja2 import Environment, FileSystemLoader
from datetime import datetime

from .scraper import OhioLegalScraper


class OhioLegalApp:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('app/templates'))

        self.data = {
                'ohio-constitution': None,
                'ohio-revised-code': None,
                'ohio-administrative-code': None
                }

        for doc in self.data:
            cache = f'{doc}.json'
            scraper = OhioLegalScraper(path=doc, cache_file=cache)
            self.data[doc] = scraper


    @cherrypy.expose
    def index(self):

        raise cherrypy.HTTPRedirect('/ohio-constitution')


    def build_page(self, doc, *args):

        base_path = (f'/{doc}/' + '/'.join(args)).rstrip('/')

        dpointer = self.data[doc].scrape_data['data']

        page_title = None
        for arg in args:
            if 'title' in dpointer[arg]:
                page_title = dpointer[arg]['title']
            if 'data' in dpointer[arg]:
                dpointer = dpointer[arg]['data']

        if 'ps' not in dpointer:
            res = []
            for key in dpointer.keys():
                if 'title' in dpointer[key]:
                    title = dpointer[key]['title']
                    res.append((key, title))
                else:
                    res.append((key,None))

            tmpl = self.env.get_template('index.j2')
            return tmpl.render(
                    {
                        'year': datetime.now().strftime('%Y'),
                        'base_url': self.data[doc].base_url,
                        'titles': res,
                        'base_path': base_path,
                        'breadcrumb': args,
                        'path': doc,
                    }
                )

        else:

            res = dpointer
            tmpl = self.env.get_template('page.j2')
            return tmpl.render(
                    {
                        'year': datetime.now().strftime('%Y'),
                        'base_url': self.data[doc].base_url,
                        'path': doc,
                        'sdata': res,
                        'page_title': page_title if page_title else args[-1],
                        'base_path': base_path,
                        'breadcrumb': args,
                    }
                )


    @cherrypy.expose
    def ohio_constitution(self, *args):

        path = 'ohio-constitution'
        return self.build_page(path, *args)


    @cherrypy.expose
    def ohio_revised_code(self, *args):

        path = 'ohio-revised-code'
        return self.build_page(path, *args)


    @cherrypy.expose
    def ohio_administrative_code(self, *args):

        path = 'ohio-administrative-code'
        return self.build_page(path, *args)


    def error_page(status, message, traceback, version):
        return "Error (%s): %s" % (status, message)

