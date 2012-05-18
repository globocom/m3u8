import os
import re
import urlparse
from urllib2 import urlopen

from m3u8.model import M3U8, Playlist
from m3u8.parser import parse, is_url

__all__ = 'M3U8', 'Playlist', 'loads', 'load', 'parse'

def loads(content):
    '''
    Given a string with a m3u8 content, returns a M3U8 object.
    Raises ValueError if invalid content
    '''
    return M3U8(content)

def load(uri):
    '''
    Retrieves the content from a given URI and returns a M3U8 object.
    Raises ValueError if invalid content or IOError if request fails.
    '''
    if is_url(uri):
        return _load_from_uri(uri)
    else:
        return _load_from_file(uri)

def _load_from_uri(uri):
    content = urlopen(uri).read().strip()
    parsed_url = urlparse.urlparse(uri)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    basepath = os.path.normpath(parsed_url.path + '/..')
    baseuri = urlparse.urljoin(prefix, basepath)
    return M3U8(content, baseuri=baseuri)

def _load_from_file(uri):
    with open(uri) as fileobj:
        raw_content = fileobj.read().strip()
    baseuri = os.path.dirname(uri)
    return M3U8(raw_content, baseuri=baseuri)

