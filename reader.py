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

def read_front_page(newspaper_url, after, before):
    """Read the front page of a newspaper."""
    text = just_content(access_page(newspaper_url))
    text = cut_between(text, after, before)
    return text

def access_page(url):
    """Access a page at a given URL."""
    page = urllib.request.urlopen(url)
    encoding = page.headers.get_param('charset')
    if encoding is None:
        encoding = 'utf-8'
    # TODO : raise a special exception if cannot be read
    return str(page.read().decode(encoding))

def just_content(page):
    """Remove every HTML from a webpage, get only the text.
    That means what we will only want the value inside of body,
    and we'll disregard any script.
    We didn't use a SoupStrainer, because we wan't a LOT of things,
    and we need to have something general enough so that we can
    (hopefully !) use it for very different websites.

    >>> just_content("<html><head>No</head><body><script>NO!</script>\
            <style>NOOOO</style><h1>Just</h1><div>this<p>text</p></div>")
    'Just this text'

    >>> just_content("<html><head></head><body><script>No</script>\
            <script>Still no</script><div>This</div>")
    'This'

    >>> just_content("<html><body><div>Well\\nHello !</div></body>")
    'Well\\tHello !'

    >>> just_content("<html><body>Well <div>hello !</div>")
    'Well hello !'

    """
    soup = BeautifulSoup(page)
    [tag.decompose() for tag in soup('script')]
    [tag.decompose() for tag in soup('style')]
    text = soup.body.get_text(separator = u' ').strip()
    # Get rid of LF and double spaces
    text = text.replace('\n','\t').replace(u'  ', u' ')
    return text

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
