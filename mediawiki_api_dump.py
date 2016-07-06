#!/usr/bin/env python3
#coding: *-*utf-8*-*


import requests
import json
import xml.etree.ElementTree as ET

def get_pages(apfrom=None):
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
    return requests.get('https://wiki.archlinux.org/api.php', params=params).json()

def get_all_pages(cache=False, save_cache=False):
    if cache:
        with open('pages.json') as f:
            return json.load(f)

    apfrom = None
    pages = []
    while True:
        result = get_pages(apfrom)
        pages.extend(result['query']['allpages'])
        if 'continue' not in result:
            break
        apfrom = result['continue']['apcontinue']

    if save_cache:
        with open('pages.json', 'w') as f:
            json.dump(pages, f)

    return pages


def split(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs

#limit 50
def get_page_by_id(pageids=[]):
    params = {
        'action': 'query',
        'pageids': '|'.join([str(x) for x in pageids]),
        'continue': '',
        'export': '',
        'exportnowrap': ''
    }
    return requests.get('https://wiki.archlinux.org/api.php', params=params).text

def merge_pages(pageids=[]):
    if not pageids:
        return


    base = ET.fromstring(get_page_by_id())
    ET.register_namespace('','http://www.mediawiki.org/xml/export-0.10/') #read out
    ns = base.tag[:base.tag.index('}')+1]


    for ids in split(pageids, 50):
        print(ids)

        root = ET.fromstring(get_page_by_id(ids))
        base.extend(root.iter(ns + 'page'))

    tree = ET.ElementTree(base)
    tree.write('articles_merged.xml', encoding='utf-8')

    #print(ET.tostring(root, encoding='utf-8').decode('utf-8'))



def main():
    pages = get_all_pages()

    merge_pages([x['pageid'] for x in pages]) #50

    #fix identation with: sed -i -e 's/^<page>/  <page>/g' articles_merged.xml

if __name__ == '__main__':
    main()
