# -*- coding: utf-8 -*-
"""This module give a simple API to read web pages,
remove irrelevant html tags, get pure text out of it
and simply render a Counter object for this words.
External modules should only have to use the read_front_page
method."""

from bs4 import BeautifulSoup
from collections import Counter
import urllib.request
import re

# Match only alphanum and hyphen (for composed words).
# Note : this will not take some names (O'Brien, for instance)
pattern = re.compile("[^\w\s-]", re.UNICODE)

def read_front_page(newspaper_url):
    """Read the front page of a newspaper."""
    return just_content(access_page(newspaper_url))

def access_page(url):
    """Access a page at a given URL."""
    page = urllib.request.urlopen(url)
    encoding = page.headers.get_param('charset')
    # TODO : raise a special exception if cannot be read
    return str(page.read().decode(encoding))

def just_content(page):
    """Remove every HTML from a webpage, get only the text.
    That means what we will only want the value inside of body,
    and we'll disregard any script.
    We didn't use a SoupStrainer, because we wan't a LOT of things,
    and we need to have something general enough so that we can
    (hopefully !) use it for very different websites."""
    soup = BeautifulSoup(page)
    while soup.script is not None:
        soup.script.decompose()
    return soup.body.get_text().strip()
