#!/usr/bin/env python3
#coding: *-*utf-8*-*

import xml.etree.ElementTree as ET
import sys


def main():
    tags = []
    depth = 0
    for event, elem in ET.iterparse(sys.stdin, ['start', 'end']):
        if event == 'end':
            depth -= 1

        if depth == 1 and elem.tag not in tags:
            tags.append(elem.tag)
            print(elem.tag)

        elem.clear()

        if event == 'start':
            depth += 1

    print(tags)


if __name__ == '__main__':
    main()
