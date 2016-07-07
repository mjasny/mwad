# mwad - mediawiki api 


This is a script for creating xml-dumps via the mediawiki api.
It is still in early development, feel free to a new [issues](https://github.com/Mattze96/mwad/issues).

Importing to @gnosygnu's offline wikipedia-reader [XOWA](https://github.com/gnosygnu/xowa) works, but some layouts/templates seem to be missing.

## Installation
#### Ubuntu
    sudo apt-get install python3-lxml
#### Archlinux
    sudo pacman -S python-lxml

You can install the `lxml` dependency via `python-pip` too.

---


## Run
    ./mediawiki_api_dump.py [args]
