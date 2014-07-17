from collections import namedtuple
import os
import posixpath
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

     `base_path`
       all urls (key and segments url) will be updated with this base_path,
       ex.:
           base_path = "http://videoserver.com/hls"

            /foo/bar/key.bin           -->  http://videoserver.com/hls/key.bin
            http://vid.com/segment1.ts -->  http://videoserver.com/hls/segment1.ts

       can be passed as parameter or setted as an attribute to ``M3U8`` object.
     `base_uri`
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

        If true, `playlists` is a list of the playlists available,
        and `iframe_playlists` is a list of the i-frame playlists available.

     `is_endlist`
        Returns true if EXT-X-ENDLIST tag present in M3U8.
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.8

      `playlists`
        If this is a variant playlist (`is_variant` is True), returns a list of
        Playlist objects

      `iframe_playlists`
        If this is a variant playlist (`is_variant` is True), returns a list of
        IFramePlaylist objects

      `playlist_type`
        A lower-case string representing the type of the playlist, which can be
        one of VOD (video on demand) or EVENT.

      `media`
        If this is a variant playlist (`is_variant` is True), returns a list of
        Media objects

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

      `base_uri`
        It is a property (getter and setter) used by
        SegmentList and Key to have absolute URIs.

      `is_i_frames_only`
        Returns true if EXT-X-I-FRAMES-ONLY tag present in M3U8.
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.12

    '''

    simple_attributes = (
        # obj attribute      # parser attribute
        ('is_variant',       'is_variant'),
        ('is_endlist',       'is_endlist'),
        ('is_i_frames_only', 'is_i_frames_only'),
        ('target_duration',  'targetduration'),
        ('media_sequence',   'media_sequence'),
        ('version',          'version'),
        ('allow_cache',      'allow_cache'),
        ('playlist_type',    'playlist_type')
        )

    def __init__(self, content=None, base_path=None, base_uri=None):
        if content is not None:
            self.data = parser.parse(content)
        else:
            self.data = {}
        self._base_uri = base_uri
        self._initialize_attributes()
        self.base_path = base_path

    def _initialize_attributes(self):
        self.key = Key(base_uri=self.base_uri, **self.data['key']) if 'key' in self.data else None
        self.segments = SegmentList([ Segment(base_uri=self.base_uri, **params)
                                      for params in self.data.get('segments', []) ])

        for attr, param in self.simple_attributes:
            setattr(self, attr, self.data.get(param))

        self.files = []
        if self.key:
            self.files.append(self.key.uri)
        self.files.extend(self.segments.uri)

        self.media = []
        for media in self.data.get('media', []):
            self.media.append(Media(uri=media.get('uri'),
                                    type=media.get('type'),
                                    group_id=media.get('group_id'),
                                    language=media.get('language'),
                                    name=media.get('name'),
                                    default=media.get('default'),
                                    autoselect=media.get('autoselect'),
                                    forced=media.get('forced'),
                                    characteristics=media.get('characteristics')))

        self.playlists = PlaylistList([ Playlist(base_uri=self.base_uri,
                                                 media=self.media,
                                                 **playlist)
                                        for playlist in self.data.get('playlists', []) ])

        self.iframe_playlists = PlaylistList()
        for ifr_pl in self.data.get('iframe_playlists', []):
            self.iframe_playlists.append(
                IFramePlaylist(base_uri=self.base_uri,
                               uri=ifr_pl['uri'],
                               iframe_stream_info=ifr_pl['iframe_stream_info'])
            )

    def __unicode__(self):
        return self.dumps()

    @property
    def base_uri(self):
        return self._base_uri

    @base_uri.setter
    def base_uri(self, new_base_uri):
        self._base_uri = new_base_uri
        self.segments.base_uri = new_base_uri

    @property
    def base_path(self):
        return self._base_path

    @base_path.setter
    def base_path(self, newbase_path):
        self._base_path = newbase_path
        self._update_base_path()

    def _update_base_path(self):
        if self._base_path is None:
            return
        if self.key:
            self.key.base_path = self.base_path
        self.segments.base_path = self.base_path
        self.playlists.base_path = self.base_path

    def add_playlist(self, playlist):
        self.is_variant = True
        self.playlists.append(playlist)

    def add_iframe_playlist(self, iframe_playlist):
        if iframe_playlist is not None:
            self.is_variant = True
            self.iframe_playlists.append(iframe_playlist)

    def add_media(self, media):
        self.media.append(media)

    def add_segment(self, segment):
        self.segments.append(segment)

    def dumps(self):
        '''
        Returns the current m3u8 as a string.
        You could also use unicode(<this obj>) or str(<this obj>)
        '''
        output = ['#EXTM3U']
        if self.media_sequence is not None:
            output.append('#EXT-X-MEDIA-SEQUENCE:' + str(self.media_sequence))
        if self.allow_cache:
            output.append('#EXT-X-ALLOW-CACHE:' + self.allow_cache.upper())
        if self.version:
            output.append('#EXT-X-VERSION:' + self.version)
        if self.key:
            output.append(str(self.key))
        if self.target_duration:
            output.append('#EXT-X-TARGETDURATION:' + int_or_float_to_string(self.target_duration))
        if not (self.playlist_type is None or self.playlist_type == ''):
            output.append(
                '#EXT-X-PLAYLIST-TYPE:%s' % str(self.playlist_type).upper())
        if self.is_i_frames_only:
            output.append('#EXT-X-I-FRAMES-ONLY')
        if self.is_variant:
            for media in self.media:
                media_out = []

                if media.uri:
                    media_out.append('URI=' + quoted(media.uri))
                if media.type:
                    media_out.append('TYPE=' + media.type)
                if media.group_id:
                    media_out.append('GROUP-ID=' + quoted(media.group_id))
                if media.language:
                    media_out.append('LANGUAGE=' + quoted(media.language))
                if media.name:
                    media_out.append('NAME=' + quoted(media.name))
                if media.default:
                    media_out.append('DEFAULT=' + media.default)
                if media.autoselect:
                    media_out.append('AUTOSELECT=' + media.autoselect)
                if media.forced:
                    media_out.append('FORCED=' + media.forced)
                if media.characteristics:
                    media_out.append('CHARACTERISTICS=' + quoted(media.characteristics))

                output.append('#EXT-X-MEDIA:' + ','.join(media_out))
            output.append(str(self.playlists))
            if self.iframe_playlists:
                output.append(str(self.iframe_playlists))

        output.append(str(self.segments))

        if self.is_endlist:
            output.append('#EXT-X-ENDLIST')

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
            if self.base_uri is None:
                raise ValueError('There can not be `absolute_uri` with no `base_uri` set')
            return _urijoin(self.base_uri, self.uri)

    @property
    def base_path(self):
        return os.path.dirname(self.uri)

    @base_path.setter
    def base_path(self, newbase_path):
        if not self.base_path:
            self.uri = "%s/%s" % (newbase_path, self.uri)
        self.uri = self.uri.replace(self.base_path, newbase_path)

class GroupedBasePathMixin(object):

    def _set_base_uri(self, new_base_uri):
        for item in self:
            item.base_uri = new_base_uri

    base_uri = property(None, _set_base_uri)

    def _set_base_path(self, newbase_path):
        for item in self:
            item.base_path = newbase_path

    base_path = property(None, _set_base_path)

class Segment(BasePathMixin):
    '''
    A video segment from a M3U8 playlist

    `uri`
      a string with the segment uri

    `title`
      title attribute from EXTINF parameter

    `duration`
      duration attribute from EXTINF paramter

    `base_uri`
      uri the key comes from in URI hierarchy. ex.: http://example.com/path/to

    `byterange`
      byterange attribute from EXT-X-BYTERANGE parameter
    '''

    def __init__(self, uri, base_uri, duration=None,
                 title=None, byterange=None):
        self.uri = uri
        self.duration = duration
        self.title = title
        self.base_uri = base_uri
        self.byterange = byterange

    def __str__(self):
        output = ['#EXTINF:%s,' % int_or_float_to_string(self.duration)]
        if self.title:
            output.append(quoted(self.title))

        output.append('\n')

        if self.byterange:
            output.append('#EXT-X-BYTERANGE:%s\n' % self.byterange)

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

    `base_uri`
      uri the key comes from in URI hierarchy. ex.: http://example.com/path/to

    `iv`
      initialization vector. a string representing a hexadecimal number. ex.: 0X12A

    '''
    def __init__(self, method, uri, base_uri, iv=None):
        self.method = method
        self.uri = uri
        self.iv = iv
        self.base_uri = base_uri

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

    Attributes:

    `stream_info` is a named tuple containing the attributes: `program_id`,
    `bandwidth`,`resolution`, `codecs` and `resolution` which is a a tuple (w, h) of integers

    `media` is a list of related Media entries.

    More info: http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.10
    '''
    def __init__(self, uri, stream_info, media, base_uri):
        self.uri = uri
        self.base_uri = base_uri

        resolution = stream_info.get('resolution')
        if resolution != None:
            values = resolution.split('x')
            resolution_pair = (int(values[0]), int(values[1]))
        else:
            resolution_pair = None

        self.stream_info = StreamInfo(bandwidth=stream_info['bandwidth'],
                                      program_id=stream_info.get('program_id'),
                                      resolution=resolution_pair,
                                      codecs=stream_info.get('codecs'))
        self.media = []
        for media_type in ('audio', 'video', 'subtitles'):
            group_id = stream_info.get(media_type)
            if not group_id:
                continue

            self.media += filter(lambda m: m.group_id == group_id, media)

    def __str__(self):
        stream_inf = []
        if self.stream_info.program_id:
            stream_inf.append('PROGRAM-ID=' + self.stream_info.program_id)
        if self.stream_info.bandwidth:
            stream_inf.append('BANDWIDTH=' + self.stream_info.bandwidth)
        if self.stream_info.resolution:
            res = str(self.stream_info.resolution[0]) + 'x' + str(self.stream_info.resolution[1])
            stream_inf.append('RESOLUTION=' + res)
        if self.stream_info.codecs:
            stream_inf.append('CODECS=' + quoted(self.stream_info.codecs))

        for media in self.media:
            media_type = media.type.upper()
            stream_inf.append('%s="%s"' % (media_type, media.group_id))

        return '#EXT-X-STREAM-INF:' + ','.join(stream_inf) + '\n' + self.uri

class IFramePlaylist(BasePathMixin):
    '''
    IFramePlaylist object representing a link to a
    variant M3U8 i-frame playlist with a specific bitrate.

    Attributes:

    `iframe_stream_info` is a named tuple containing the attributes:
     `program_id`, `bandwidth`, `codecs` and `resolution` which
     is a tuple (w, h) of integers

    More info: http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.13
    '''
    def __init__(self, base_uri, uri, iframe_stream_info):
        self.uri = uri
        self.base_uri = base_uri

        resolution = iframe_stream_info.get('resolution')
        if resolution is not None:
            values = resolution.split('x')
            resolution_pair = (int(values[0]), int(values[1]))
        else:
            resolution_pair = None

        self.iframe_stream_info = StreamInfo(
            bandwidth=iframe_stream_info.get('bandwidth'),
            program_id=iframe_stream_info.get('program_id'),
            resolution=resolution_pair,
            codecs=iframe_stream_info.get('codecs')
        )

    def __str__(self):
        iframe_stream_inf = []
        if self.iframe_stream_info.program_id:
            iframe_stream_inf.append('PROGRAM-ID=' +
                                     self.iframe_stream_info.program_id)
        if self.iframe_stream_info.bandwidth:
            iframe_stream_inf.append('BANDWIDTH=' +
                                     self.iframe_stream_info.bandwidth)
        if self.iframe_stream_info.resolution:
            res = (str(self.iframe_stream_info.resolution[0]) + 'x' +
                   str(self.iframe_stream_info.resolution[1]))
            iframe_stream_inf.append('RESOLUTION=' + res)
        if self.iframe_stream_info.codecs:
            iframe_stream_inf.append('CODECS=' +
                                     quoted(self.iframe_stream_info.codecs))
        if self.uri:
            iframe_stream_inf.append('URI=' + quoted(self.uri))

        return '#EXT-X-I-FRAME-STREAM-INF:' + ','.join(iframe_stream_inf)

StreamInfo = namedtuple('StreamInfo', ['bandwidth', 'program_id', 'resolution', 'codecs'])
Media = namedtuple('Media', ['uri', 'type', 'group_id', 'language', 'name',
                             'default', 'autoselect', 'forced', 'characteristics'])

class PlaylistList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(playlist) for playlist in self]
        return '\n'.join(output)


def denormalize_attribute(attribute):
    return attribute.replace('_','-').upper()

def quoted(string):
    return '"%s"' % string

def _urijoin(base_uri, path):
    if parser.is_url(base_uri):
        parsed_url = urlparse.urlparse(base_uri)
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        new_path = posixpath.normpath(parsed_url.path + '/' + path)
        return urlparse.urljoin(prefix, new_path.strip('/'))
    else:
        return os.path.normpath(os.path.join(base_uri, path.strip('/')))

def int_or_float_to_string(number):
    return str(int(number)) if number == math.floor(number) else str(number)
