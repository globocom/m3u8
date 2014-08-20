# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import os
import posixpath
import urlparse
from urllib2 import urlopen

from m3u8.model import M3U8, Playlist, IFramePlaylist, Media, Segment
from m3u8.parser import parse, is_url

__all__ = ('M3U8', 'Playlist', 'IFramePlaylist', 'Media',
           'Segment', 'loads', 'load', 'parse')

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
    opened_url = urlopen(uri)
    content = opened_url.read().strip()
    parsed_url = urlparse.urlparse(opened_url.geturl())
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = posixpath.normpath(parsed_url.path + '/..')
    base_uri = urlparse.urljoin(prefix, base_path)
    return M3U8(content, base_uri=base_uri)

def _load_from_file(uri):
    with open(uri, 'r') as fileobj:
        raw_content = fileobj.read().strip()
    base_uri = os.path.dirname(uri)
    return M3U8(raw_content, base_uri=base_uri)

