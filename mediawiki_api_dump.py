#!/usr/bin/env python3
#-*-coding:utf-8-*-

import argparse
import logging
import urllib.parse
import requests
import json
import re

parser = argparse.ArgumentParser(
    description = 'Create a wiki xml-dump via api.php'
)

parser.add_argument('-v', '--verbose', action='count', default=0, help='verbose level... repeat up to three times\n')
parser.add_argument('-n', '--name', help='name of the wiki for filename etc.\n')
parser.add_argument('-l', '--log', help='specify log-file.\n')
parser.add_argument('wiki_url', metavar='url', help='download url\n') #nargs='+',

args = parser.parse_args()

logFormatter = logging.Formatter('%(asctime)s - %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

if args.log:
    fileHandler = logging.FileHandler(args.log)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(max(3 - args.verbose, 0) * 10)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
logging.getLogger('requests').setLevel(logging.CRITICAL)

logging.info('Arguments: %s', str(vars(args)))



class Dumper():
    def __init__(self, wiki, api):
        self.wiki = wiki
        self.api = api
        self.writer = None
        self.pages_per_request = 50

    def start(self):
        pageids = self.get_pageids()
        self.merge_pages(pageids)
        logging.info('Done')


    def xml_writer(self, filename):
        with open(filename, 'w') as f:
            try:
                while True:
                    line = (yield)
                    f.write(line)
            except GeneratorExit:
                logging.info('File: %s done.', filename)
                pass

    def merge_pages(self, pageids=[]):
        if not pageids:
            return

        self.writer = self.xml_writer('{0}-pages-articles.xml'.format(self.wiki))
        next(self.writer)

        page = self.mw_export_pageids()

        self.writer.send(re.search('(<mediawiki.*>)', page).group(0))
        self.writer.send(re.search('(\s*?<siteinfo>.*?<\/siteinfo>)', page, re.DOTALL).group(0))

        for ids in self.__split_list(pageids, self.pages_per_request):
            logging.info('Current ids: %s', str(ids))
            page = self.mw_export_pageids(ids)
            for page in re.finditer('(\s*?<page>.*?<\/page>)', page, re.DOTALL):
                self.writer.send(page.group(0))

        self.writer.send('\n</mediawiki>\n')
        self.writer.close()


    def mw_export_pageids(self, pageids=[]):
        params = {
            'action': 'query',
            'pageids': '|'.join([str(x) for x in pageids]),
            'continue': '',
            'export': '',
            'exportnowrap': ''
        }
        r = requests.get(self.api, params=params)
        logging.info('API: %s', r.url)
        return r.text

    def mw_list_allpages(self, apfrom=None):
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': 500,
            'continue': '',
            'format': 'json',
            #'apfilterredir': 'nonredirects'
        }
        if apfrom:
            params.update({
                'apfrom': apfrom
            })
        r = requests.get(self.api, params=params)
        logging.info('API: %s', r.url)
        return r.json()

    def get_pageids(self):
        apfrom = None
        pageids = []
        while True:
            result = self.mw_list_allpages(apfrom)
            pageids.extend([x['pageid'] for x in result['query']['allpages']])
            if 'continue' not in result:
                break
            apfrom = result['continue']['apcontinue']
        logging.info('PageIds: %s', str(pageids))
        return pageids

    def __split_list(self, l, n):
         arrs = []
         while len(l) > n:
             sl = l[:n]
             arrs.append(sl)
             l = l[n:]
         arrs.append(l)
         return arrs


if __name__ == '__main__':
    API_URL = urllib.parse.urljoin(args.wiki_url, 'api.php')
    WIKI_NAME = args.name or urllib.parse.urlparse(args.wiki_url).netloc

    dumper = Dumper(WIKI_NAME, API_URL)
    dumper.start()
    #main()
    #test()
