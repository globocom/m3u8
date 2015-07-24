# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import sys
PYTHON_MAJOR_VERSION = sys.version_info

import os
import posixpath

try:
    import urlparse as url_parser
    import urllib2
    urlopen = urllib2.urlopen
except ImportError:
    import urllib.parse as url_parser
    from urllib.request import urlopen as url_opener
    urlopen = url_opener


from m3u8.model import M3U8, Playlist, IFramePlaylist, Media, Segment
from m3u8.parser import parse, is_url, ParseError

__all__ = ('M3U8', 'Playlist', 'IFramePlaylist', 'Media',
           'Segment', 'loads', 'load', 'parse', 'ParseError')

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

# Support for python3 inspired by https://github.com/szemtiv/m3u8/
def _load_from_uri(uri):
    resource = urlopen(uri)
    base_uri = _parsed_url(_url_for(uri))
    if PYTHON_MAJOR_VERSION < (3,):
        content = _read_python2x(resource)
    else:
        content = _read_python3x(resource)
    return M3U8(content, base_uri=base_uri)

def _url_for(uri):
    return urlopen(uri).geturl()

def _parsed_url(url):
    parsed_url = url_parser.urlparse(url)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = posixpath.normpath(parsed_url.path + '/..')
    return url_parser.urljoin(prefix, base_path)

def _read_python2x(resource):
    return resource.read().strip()

def _read_python3x(resource):
    return  resource.read().decode(resource.headers.get_content_charset(failobj="utf-8"))

def _load_from_file(uri):
    with open(uri) as fileobj:
        raw_content = fileobj.read().strip()
    base_uri = os.path.dirname(uri)
    return M3U8(raw_content, base_uri=base_uri)

