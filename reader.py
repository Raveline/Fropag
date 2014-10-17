# -*- coding: utf-8 -*-
"""This module give a simple API to read web pages,
remove irrelevant html tags, get pure text out of it
and simply render a Counter object for this words.
External modules should only have to use the read_front_page
method."""

from bs4 import BeautifulSoup
import urllib.request
from urllib.error import HTTPError
import os

HTTP_PREFIX = "http://"

class UnreadablePageException(Exception):
    '''This exception should be raised when a frontpage
    cannot be read. The exception should carry a root
    cause, so it can be caught and logged.'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def unprefixed_url(newspaper_url):
    """Given a string starting with "http://",
    return the URL without the protocol.
    Note : this should be improved to handle
    https and possiply other protocols.

    >>> unprefixed_url("http://www.google.com")
    'www.google.com'
    """
    return newspaper_url[len(HTTP_PREFIX):]

def get_previous_frontpage(url):
    """Read the last recorded version of this frontpage,
    that should have been saved in the corpus directory.
    If it cannot be found, will return None."""
    dest = os.path.join("corpus", unprefixed_url(url))
    if os.path.exists(dest):
        with open(dest, 'r') as previous_file:
            return previous_file.read()

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
    for new_tag in new.find_all(True):
        if new_tag in tags_of_previous:
            to_remove.append(new_tag)
    [tag.decompose() for tag in to_remove]

def extract_content(previous, new):
    """Get two HTML documents, previous and new and try to
    transform them to BeautifulSoup.
    If the previous one exists, compare it to the new one, to
    remove any similarities - this will allow us to remove most
    of the template of the page.
    Then, get the text of the document."""
    new = BeautifulSoup(new)
    extract_script_and_style(new)
    if previous is not None:
        previous = BeautifulSoup(previous)
        extract_script_and_style(previous)
        compare(previous, new)
    return new.get_text(separator=u' ').strip()

def read_front_page(newspaper_url):
    """Read the front page of a newspaper."""
    raw_html = access_page(newspaper_url)
    previous = get_previous_frontpage(newspaper_url)
    text = extract_content(previous, raw_html)
    # Save the file in the corpus folder to be able
    # to compare it with the next version
    save_file(newspaper_url, raw_html)
    return text

def save_file(url, text):
    '''Save a version of an HTML version, given its url
    and its content, in the "corpus" directory.'''
    dest = os.path.join("corpus", unprefixed_url(url))
    with open(dest, 'w') as saving_file:
        saving_file.write(text)

def access_page(url):
    """Access a page at a given URL."""
    try:
        page = urllib.request.urlopen(url)
    except HTTPError as error_info:
        error = 'Could not read the page at {}, got\
                      an HTTPError. {}'.format(url, str(error_info))
        raise UnreadablePageException(error)
    encoding = page.headers.get_param('charset')
    if encoding is None:
        encoding = 'utf-8'
    try:
        result = str(page.read().decode(encoding))
        return result
    except UnicodeDecodeError as exc:
        error = 'Could not read the page at {} with encoding {}.\
                       Got the exception : {}'.format(url, encoding, str(exc))
        raise UnreadablePageException(error)

def cut_between(text, from_t, to_t):
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

    from_pos = text.find(from_t)
    to_pos = text.find(to_t)
    if from_pos == -1:
        from_pos = 0
    else:
        from_pos = from_pos + len(from_t)
    if to_pos == -1:
        to_pos = len(text)
    return text[from_pos:to_pos].strip()
