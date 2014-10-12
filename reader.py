# -*- coding: utf-8 -*-
"""This module give a simple API to read web pages,
remove irrelevant html tags, get pure text out of it
and simply render a Counter object for this words.
External modules should only have to use the read_front_page
method."""

from bs4 import BeautifulSoup, Tag, NavigableString
from collections import Counter
import urllib.request
import re
import os

httpPrefix = "http://"

def unprefixed_url(newspaper_url):
    return newspaper_url[len(httpPrefix):]

def get_previous_frontpage(url):
    dest= os.path.join("corpus", unprefixed_url(url))
    if os.path.exists(dest):
        with open(dest, 'r') as f:
            return f.read()

def extract_script_and_style(soup):
    """Remove the script and style tag from an HTML document
    in BeautifulSoup format.
    >>> soup = BeautifulSoup("<script>N</script><style></style><div>This</div>")
    >>> extract_script_and_style(soup)
    >>> str(soup)
    '<div>This</div>'
    """
    [tag.decompose() for tag in soup('script')]
    [tag.decompose() for tag in soup('style')]

def compare(previous, new):
    """Compare two HTML documents in BeautifulSoup format to remove any
    similar tags from the second one.
    This allow comparing two frontpages from one day to the next,
    and remove everything that is pure templating and column names.

    >>> doc1 = BeautifulSoup('<html><body><div class="container">\
    <div class="menu"><a>Choice1</a><a>Choice2</a><a>Choice3</a>\
    </div><div class="content">One text.</div></body></html>')
    >>> doc2 = BeautifulSoup('<html><body><div class="container">\
    <div class="menu"><a>Choice1</a><a>Choice2</a><a>Choice3</a>\
    </div><div class="content">Another text.</div></body></html>')
    >>> compare(doc1, doc2)
    >>> doc2.get_text().strip()
    'Another text.'
    """
    to_remove = []
    tags_of_previous = previous.find_all(True)
    for n in new.find_all(True):
        if n in tags_of_previous:
            to_remove.append(n)
    [tag.decompose() for tag in to_remove]

def extract_content(previous, new):
    new = BeautifulSoup(new)
    extract_script_and_style(new)
    if previous is not None:
        previous = BeautifulSoup(previous)
        extract_script_and_style(previous)
        compare(previous, new)
    return new.get_text(separator = u' ').strip()

def read_front_page(newspaper_url, after, before):
    """Read the front page of a newspaper."""
    raw_html = access_page(newspaper_url)
    previous = get_previous_frontpage(newspaper_url)
    text = extract_content(previous, raw_html)
    # Save the file in the corpus folder to be able
    # to compare it with the next version
    save_file(newspaper_url, raw_html)
    return text

def save_file(url, text):
    dest = os.path.join("corpus", unprefixed_url(url))
    with open(dest, 'w') as f:
        f.write(text)

def access_page(url):
    """Access a page at a given URL."""
    page = urllib.request.urlopen(url)
    encoding = page.headers.get_param('charset')
    if encoding is None:
        encoding = 'utf-8'
    # TODO : raise a special exception if cannot be read
    return str(page.read().decode(encoding))


def cut_between(text, fromT, toT):
    """Only keep a text between FROM value and TO value.
    If FROM does not exist, start from beginning. 
    If END does not exist, keep till the end.

    >>> cut_between('Shall I compare thee ? To...', 'compare', '?')
    'thee'

    >>> cut_between('Shall I compare thee', 'burg', 'thee')
    'Shall I compare'

    >>> cut_between('Shall I compare thee to a summer day', 'compare', 'burg')
    'thee to a summer day'
    """

    from_pos = text.find(fromT)
    to_pos = text.find(toT)
    if from_pos == -1:
        from_pos = 0
    else:
        from_pos = from_pos + len(fromT)
    if to_pos == -1:
        to_pos = len(text)
    return text[from_pos:to_pos].strip()
