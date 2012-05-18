import os
import re
import urlparse
from urllib2 import urlopen

from m3u8.model import M3U8, Playlist
from m3u8.parser import parse

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
    if re.match(r'https?://', uri):
        return _load_from_uri(uri)
    else:
        return _load_from_file(uri)

def _load_from_uri(uri):
    parsed_url = urlparse.urlparse(uri)
    raw_content = urlopen(uri).read().strip()
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    basepath = os.path.normpath(parsed_url.path + '/..')
    content = _change_to_absolute_paths(raw_content, basepath, prefix)
    return M3U8(content)

def _load_from_file(uri):
    with open(uri) as fileobj:
        raw_content = fileobj.read().strip()
    prefix = ''
    basepath = os.path.dirname(uri)
    content = _change_to_absolute_paths(raw_content, basepath, prefix)
    return M3U8(content)

def _change_to_absolute_paths(content, basepath, prefix):
    '''
    Replaces relative chunk paths to absolute ones. Example:

    >>> m3u8_content = '#EXTINF:123,\n../entire2.ts'
    >>> _change_to_absolute_paths(m3u8_content, '/path/to', 'http://example.com')
    '#EXTINF:123,\nhttp://example.com/path/entire2.ts'

    '''
    lines = content.split('\n')
    line_before = lines[0].strip()
    result = [line_before]
    for line in lines[1:]:
        line = line.strip()
        is_chunk = line_before.startswith('#EXTINF') and line.endswith('.ts')
        is_relative = not re.match(r'https?://', line.strip())
        if is_chunk and is_relative:
            line = prefix + os.path.normpath(basepath + '/' + line)
        line_before = line
        result.append(line)
    return '\n'.join(result)
