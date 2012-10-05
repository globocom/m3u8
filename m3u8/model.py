from collections import namedtuple
import os
import errno
import math
import urlparse
import re

from m3u8 import parser


class M3U8(object):
    '''
    Represents a single M3U8 playlist. Should be instantiated with
    the content as string.

    Parameters:

     `content`
       the m3u8 content as string

     `basepath`
       all urls (key and segments url) will be updated with this basepath,
       ex.:
           basepath = "http://videoserver.com/hls"

            /foo/bar/key.bin           -->  http://videoserver.com/hls/key.bin
            http://vid.com/segment1.ts -->  http://videoserver.com/hls/segment1.ts

       can be passed as parameter or setted as an attribute to ``M3U8`` object.
     `baseuri`
      uri the playlist comes from. it is propagated to SegmentList and Key
      ex.: http://example.com/path/to

    Attributes:

     `key`
       it's a `Key` object, the EXT-X-KEY from m3u8. Or None

     `segments`
       a `SegmentList` object, represents the list of `Segment`s from this playlist

     `is_variant`
        Returns true if this M3U8 is a variant playlist, with links to
        other M3U8s with different bitrates.

        If true, `playlists` if a list of the playlists available.

      `playlists`
        If this is a variant playlist (`is_variant` is True), returns a list of
        Playlist objects

      `target_duration`
        Returns the EXT-X-TARGETDURATION as an integer
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.2

      `media_sequence`
        Returns the EXT-X-MEDIA-SEQUENCE as an integer
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.3

      `version`
        Return the EXT-X-VERSION as is

      `allow_cache`
        Return the EXT-X-ALLOW-CACHE as is

      `files`
        Returns an iterable with all files from playlist, in order. This includes
        segments and key uri, if present.

      `baseuri`
        It is a property (getter and setter) used by
        SegmentList and Key to have absolute URIs.

    '''

    simple_attributes = (
        # obj attribute      # parser attribute
        ('is_variant',       'is_variant'),
        ('target_duration',  'targetduration'),
        ('media_sequence',   'media_sequence'),
        ('version',          'version'),
        ('allow_cache',      'allow_cache'),
        )

    def __init__(self, content=None, basepath=None, baseuri=None):
        if content is not None:
            self.data = parser.parse(content)
        else:
            self.data = {}
        self._baseuri = baseuri
        self._initialize_attributes()
        self.basepath = basepath

    def _initialize_attributes(self):
        self.key = Key(baseuri=self.baseuri, **self.data['key']) if 'key' in self.data else None
        self.segments = SegmentList([ Segment(baseuri=self.baseuri, **params)
                                      for params in self.data.get('segments', []) ])

        for attr, param in self.simple_attributes:
            setattr(self, attr, self.data.get(param))

        self.files = []
        if self.key:
            self.files.append(self.key.uri)
        self.files.extend(self.segments.uri)

        self.playlists = PlaylistList([ Playlist(baseuri=self.baseuri, **playlist)
                                        for playlist in self.data.get('playlists', []) ])

    def __unicode__(self):
        return self.dumps()

    @property
    def baseuri(self):
        return self._baseuri
    
    @baseuri.setter
    def baseuri(self, new_baseuri):
        self._baseuri = new_baseuri
        self.segments.baseuri = new_baseuri

    @property
    def basepath(self):
        return self._basepath

    @basepath.setter
    def basepath(self, newbasepath):
        self._basepath = newbasepath
        self._update_basepath()

    def _update_basepath(self):
        if self._basepath is None:
            return
        if self.key:
            self.key.basepath = self.basepath
        self.segments.basepath = self.basepath
        self.playlists.basepath = self.basepath

    def add_playlist(self, playlist):
        self.is_variant = True
        self.playlists.append(playlist)

    def dumps(self):
        '''
        Returns the current m3u8 as a string.
        You could also use unicode(<this obj>) or str(<this obj>)
        '''
        output = ['#EXTM3U']
        if self.media_sequence:
            output.append('#EXT-X-MEDIA-SEQUENCE:' + str(self.media_sequence))
        if self.allow_cache:
            output.append('#EXT-X-ALLOW-CACHE:' + self.allow_cache.upper())
        if self.version:
            output.append('#EXT-X-VERSION:' + self.version)
        if self.key:
            output.append(str(self.key))
        if self.target_duration:
            output.append('#EXT-X-TARGETDURATION:' + int_or_float_to_string(self.target_duration))
        if self.is_variant:
            output.append(str(self.playlists))

        output.append(str(self.segments))

        return '\n'.join(output)

    def dump(self, filename):
        '''
        Saves the current m3u8 to ``filename``
        '''
        self._create_sub_directories(filename)

        with open(filename, 'w') as fileobj:
            fileobj.write(self.dumps())

    def _create_sub_directories(self, filename):
        basename = os.path.dirname(filename)
        try:
            os.makedirs(basename)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

class BasePathMixin(object):

    @property
    def absolute_uri(self):
        if parser.is_url(self.uri):
            return self.uri
        else:
            if self.baseuri is None:
                raise ValueError('There can not be `absolute_uri` with no `baseuri` set')
            return _urijoin(self.baseuri, self.uri)

    @property
    def basepath(self):
        return os.path.dirname(self.uri)

    @basepath.setter
    def basepath(self, newbasepath):
        self.uri = self.uri.replace(self.basepath, newbasepath)

class GroupedBasePathMixin(object):

    def _set_baseuri(self, new_baseuri):
        for item in self:
            item.baseuri = new_baseuri

    baseuri = property(None, _set_baseuri)

    def _set_basepath(self, newbasepath):
        for item in self:
            item.basepath = newbasepath

    basepath = property(None, _set_basepath)

class Segment(BasePathMixin):
    '''
    A video segment from a M3U8 playlist

    `uri`
      a string with the segment uri

    `title`
      title attribute from EXTINF parameter

    `duration`
      duration attribute from EXTINF paramter

    `baseuri`
      uri the key comes from in URI hierarchy. ex.: http://example.com/path/to
    '''

    def __init__(self, uri, baseuri, duration=None, title=None):
        self.uri = uri
        self.duration = duration
        self.title = title
        self.baseuri = baseuri

    def __str__(self):
        output = ['#EXTINF:%s,' % int_or_float_to_string(self.duration)]
        if self.title:
            output.append(quoted(self.title))

        output.append('\n')
        output.append(self.uri)

        return ''.join(output)


class SegmentList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(segment) for segment in self]
        return '\n'.join(output)

    @property
    def uri(self):
        return [seg.uri for seg in self]

class Key(BasePathMixin):
    '''
    Key used to encrypt the segments in a m3u8 playlist (EXT-X-KEY)

    `method`
      is a string. ex.: "AES-128"

    `uri`
      is a string. ex:: "https://priv.example.com/key.php?r=52"

    `baseuri`
      uri the key comes from in URI hierarchy. ex.: http://example.com/path/to

    `iv`
      initialization vector. a string representing a hexadecimal number. ex.: 0X12A

    '''
    def __init__(self, method, uri, baseuri, iv=None):
        self.method = method
        self.uri = uri
        self.iv = iv
        self.baseuri = baseuri

    def __str__(self):
        output = [
            'METHOD=%s' % self.method,
            'URI="%s"' % self.uri,
            ]
        if self.iv:
            output.append('IV=%s' % self.iv)

        return '#EXT-X-KEY:' + ','.join(output)


class Playlist(BasePathMixin):
    '''
    Playlist object representing a link to a variant M3U8 with a specific bitrate.
    Each `stream_info` attribute has: `program_id`, `bandwidth` and `codecs`

    More info: http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.10
    '''
    def __init__(self, uri, stream_info, baseuri):
        self.uri = uri
        self.baseuri = baseuri
        self.stream_info = StreamInfo(bandwidth=stream_info['bandwidth'],
                                      program_id=stream_info.get('program_id'),
                                      codecs=stream_info.get('codecs'))

    def __str__(self):
        stream_inf = []
        if self.stream_info.program_id:
            stream_inf.append('PROGRAM-ID=' + self.stream_info.program_id)
        if self.stream_info.bandwidth:
            stream_inf.append('BANDWIDTH=' + self.stream_info.bandwidth)
        if self.stream_info.codecs:
            stream_inf.append('CODECS=' + quoted(self.stream_info.codecs))
        return '#EXT-X-STREAM-INF:' + ','.join(stream_inf) + '\n' + self.uri

StreamInfo = namedtuple('StreamInfo', ['bandwidth', 'program_id', 'codecs'])

class PlaylistList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(playlist) for playlist in self]
        return '\n'.join(output)


def denormalize_attribute(attribute):
    return attribute.replace('_','-').upper()

def quoted(string):
    return '"%s"' % string

def _urijoin(baseuri, path):
    if parser.is_url(baseuri):
        parsed_url = urlparse.urlparse(baseuri)
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        new_path = os.path.normpath(parsed_url.path + '/' + path)
        return urlparse.urljoin(prefix, new_path.strip('/'))
    else:
        return os.path.normpath(os.path.join(baseuri, path.strip('/')))

def int_or_float_to_string(number):
    return str(int(number)) if number == math.floor(number) else str(number)
