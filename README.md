# ohio-law-scraper

A BeautifulSoup4 web scraper that converts the Ohio Constitution, Ohio Revised Code, and Ohio Administrative Code into JSON files

Also provides a simple CherryPy web interface.

## Usage

### Scraping a document

Note: The Ohio Revised Code is *huge*. It takes **days** to scrape with a 2-second interval. Scrape respectfully. The resulting JSON file is well over 50MB. The Ohio Administrative Code is around 1/4 the size of the Revised Code.

In a python shell, configure and run the scraper from directory `ohio-law-scraper/app`:

```
from scraper import *
sc = OhioLegalScraper(path='ohio-revised-code', cache\_file='ohio-revised\_code.json')
sc.scrape()
```

Use one of three URLs to scrape: `ohio-constitution`, `ohio-revised-code`, or `ohio-administrative-code`

Cache file is overwritten after every page request, files written to `app` directory unless otherwise specified.

### Running the web server

From the `ohio-law-scraper` directory,

```
python run.py
```

The web application checks this directory for cache files, so if you created them in the `app` directory, they need to be moved.
