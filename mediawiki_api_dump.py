#!/usr/bin/env python3
#-*-coding:utf-8-*-

'''mediawiki_api_dump.py: Creates a xml dump of all pages from the given wiki-url'''

__author__      = 'https://github.com/Mattze96'
__copyright__   = 'Copyright 2016, Planet Earth'

import argparse
import logging
import urllib.parse
import requests
import json
import re
import time
import sys
import bz2

parser = argparse.ArgumentParser(
    description = 'Create a wiki xml-dump via api.php'
)

parser.add_argument('-v', '--verbose', action='count', default=0, help='verbose level... repeat up to three times\n')
parser.add_argument('-n', '--name', help='name of the wiki for filename etc.\n')
parser.add_argument('-l', '--log', help='specify log-file.\n')
parser.add_argument('-c', '--compress', action='store_true', help='compress output file with bz2')
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
    def __init__(self, wiki, api, compress):
        self.wiki = wiki
        self.api = api
        self.compress = compress
        self.writer = None
        self.pages_per_request = 50

    def start(self):
        nss = self.get_nsids()
        pageids = self.get_pageids(nss)
        self.merge_pages(pageids)
        logging.info('Done')

    def get_nsids(self):
        nss = self.mw_siteinfo_namespaces()['query']['namespaces']
        #Why not negative ??
        return [x['id'] for x in nss.values() if x['id'] >= 0]

    def xml_writer(self, filename):
        if self.compress:
            with bz2.open(filename+'.bz2', 'w') as f:
                try:
                    while True:
                        line = (yield)
                        f.write(line.encode('utf-8'))
                except GeneratorExit:
                    pass
            logging.info('File: %s.bz2 done.', filename)
        else:
            with open(filename, 'w') as f:
                try:
                    while True:
                        line = (yield)
                        f.write(line)
                except GeneratorExit:
                    pass
            logging.info('File: %s done.', filename)

    def merge_pages(self, pageids=[]):
        if not pageids:
            return

        self.writer = self.xml_writer('{0}-{1}-pages-articles.xml'.format(self.wiki, time.strftime('%Y%m%d')))
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

    def mw_list_allpages(self, apfrom=None, ns=0):
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': 500,
            'continue': '',
            'format': 'json',
            'apnamespace': ns
        }
        if apfrom:
            params.update({
                'apfrom': apfrom
            })
        r = requests.get(self.api, params=params)
        logging.info('API: %s', r.url)
        return r.json()

    def mw_siteinfo_namespaces(self):
            params = {
                'action': 'query',
                'meta': 'siteinfo',
                'siprop': 'namespaces',
                'format': 'json',
            }
            r = requests.get(self.api, params=params)
            logging.info('API: %s', r.url)
            return r.json()

    def get_pageids(self, nss=[0]):
        pageids = []
        for ns in nss:
            apfrom = None
            while True:
                result = self.mw_list_allpages(apfrom, ns)
                pageids.extend([x['pageid'] for x in result['query']['allpages']])
                if 'continue' not in result:
                    break
                apfrom = result['continue']['apcontinue']
        pageids.sort()
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
    COMPRESS = args.compress

    dumper = Dumper(WIKI_NAME, API_URL, COMPRESS)
    dumper.start()
    #main()
    #test()
