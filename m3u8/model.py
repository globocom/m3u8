# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

from collections import namedtuple
import os
import errno
import math

from m3u8.protocol import ext_x_start
from m3u8.parser import parse, format_date_time
from m3u8.mixins import BasePathMixin, GroupedBasePathMixin


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

     `keys`
       Returns the list of `Key` objects used to encrypt the segments from m3u8.
       It covers the whole list of possible situations when encryption either is
       used or not.

       1. No encryption.
       `keys` list will only contain a `None` element.

       2. Encryption enabled for all segments.
       `keys` list will contain the key used for the segments.

       3. No encryption for first element(s), encryption is applied afterwards
       `keys` list will contain `None` and the key used for the rest of segments.

       4. Multiple keys used during the m3u8 manifest.
       `keys` list will contain the key used for each set of segments.

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

      `program_date_time`
        Returns the EXT-X-PROGRAM-DATE-TIME as a string
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.5

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

      `is_independent_segments`
        Returns true if EXT-X-INDEPENDENT-SEGMENTS tag present in M3U8.
        https://tools.ietf.org/html/draft-pantos-http-live-streaming-13#section-3.4.16

    '''

    simple_attributes = (
        # obj attribute      # parser attribute
        ('is_variant',       'is_variant'),
        ('is_endlist',       'is_endlist'),
        ('is_i_frames_only', 'is_i_frames_only'),
        ('target_duration',  'targetduration'),
        ('media_sequence',   'media_sequence'),
        ('program_date_time',   'program_date_time'),
        ('is_independent_segments', 'is_independent_segments'),
        ('version',          'version'),
        ('allow_cache',      'allow_cache'),
        ('playlist_type',    'playlist_type'),
        ('discontinuity_sequence', 'discontinuity_sequence')
    )

    def __init__(self, content=None, base_path=None, base_uri=None, strict=False):
        if content is not None:
            self.data = parse(content, strict)
        else:
            self.data = {}
        self._base_uri = base_uri
        if self._base_uri:
            if not self._base_uri.endswith('/'):
                self._base_uri += '/'

        self._initialize_attributes()
        self.base_path = base_path


    def _initialize_attributes(self):
        self.keys = [ Key(base_uri=self.base_uri, **params) if params else None
                      for params in self.data.get('keys', []) ]
        self.segments = SegmentList([ Segment(base_uri=self.base_uri, keyobject=find_key(segment.get('key', {}), self.keys), **segment)
                                      for segment in self.data.get('segments', []) ])
        #self.keys = get_uniques([ segment.key for segment in self.segments ])
        for attr, param in self.simple_attributes:
            setattr(self, attr, self.data.get(param))

        self.files = []
        for key in self.keys:
            # Avoid None key, it could be the first one, don't repeat them
            if key and key.uri not in self.files:
                self.files.append(key.uri)
        self.files.extend(self.segments.uri)

        self.media = MediaList([ Media(base_uri=self.base_uri, **media)
                                 for media in self.data.get('media', []) ])

        self.playlists = PlaylistList([ Playlist(base_uri=self.base_uri, media=self.media, **playlist)
                                        for playlist in self.data.get('playlists', []) ])

        self.iframe_playlists = PlaylistList()
        for ifr_pl in self.data.get('iframe_playlists', []):
            self.iframe_playlists.append(IFramePlaylist(base_uri=self.base_uri,
                                         uri=ifr_pl['uri'],
                                         iframe_stream_info=ifr_pl['iframe_stream_info'])
                                        )
        self.segment_map = self.data.get('segment_map')

        start = self.data.get('start', None)
        self.start = start and Start(**start)

    def __unicode__(self):
        return self.dumps()

    @property
    def base_uri(self):
        return self._base_uri

    @base_uri.setter
    def base_uri(self, new_base_uri):
        self._base_uri = new_base_uri
        self.media.base_uri = new_base_uri
        self.playlists.base_uri = new_base_uri
        self.segments.base_uri = new_base_uri
        for key in self.keys:
            if key:
                key.base_uri = new_base_uri

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
        for key in self.keys:
            if key:
                key.base_path = self._base_path
        self.media.base_path = self._base_path
        self.segments.base_path = self._base_path
        self.playlists.base_path = self._base_path


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
        if self.is_independent_segments:
            output.append('#EXT-X-INDEPENDENT-SEGMENTS')
        if self.media_sequence:
            output.append('#EXT-X-MEDIA-SEQUENCE:' + str(self.media_sequence))
        if self.discontinuity_sequence:
            output.append('#EXT-X-DISCONTINUITY-SEQUENCE:{}'.format(
                int_or_float_to_string(self.discontinuity_sequence)))
        if self.allow_cache:
            output.append('#EXT-X-ALLOW-CACHE:' + self.allow_cache.upper())
        if self.version:
            output.append('#EXT-X-VERSION:' + self.version)
        if self.target_duration:
            output.append('#EXT-X-TARGETDURATION:' +
                          int_or_float_to_string(self.target_duration))
        if self.program_date_time is not None:
            output.append('#EXT-X-PROGRAM-DATE-TIME:' + format_date_time(self.program_date_time))
        if not (self.playlist_type is None or self.playlist_type == ''):
            output.append('#EXT-X-PLAYLIST-TYPE:%s' % str(self.playlist_type).upper())
        if self.start:
            output.append(str(self.start))
        if self.is_i_frames_only:
            output.append('#EXT-X-I-FRAMES-ONLY')
        if self.is_variant:
            if self.media:
                output.append(str(self.media))
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
            if basename:
                os.makedirs(basename)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise


class Segment(BasePathMixin):
    '''
    A video segment from a M3U8 playlist

    `uri`
      a string with the segment uri

    `title`
      title attribute from EXTINF parameter

    `program_date_time`
      Returns the EXT-X-PROGRAM-DATE-TIME as a datetime
      http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.5

    `discontinuity`
      Returns a boolean indicating if a EXT-X-DISCONTINUITY tag exists
      http://tools.ietf.org/html/draft-pantos-http-live-streaming-13#section-3.4.11

    `cue_out`
      Returns a boolean indicating if a EXT-X-CUE-OUT-CONT tag exists

    `scte35`
      Base64 encoded SCTE35 metadata if available

    `scte35_duration`
      Planned SCTE35 duration

    `duration`
      duration attribute from EXTINF parameter

    `base_uri`
      uri the key comes from in URI hierarchy. ex.: http://example.com/path/to

    `byterange`
      byterange attribute from EXT-X-BYTERANGE parameter

    `key`
      Key used to encrypt the segment (EXT-X-KEY)
    '''

    def __init__(self, uri, base_uri, program_date_time=None, duration=None,
                 title=None, byterange=None, cue_out=False, discontinuity=False, key=None,
                 scte35=None, scte35_duration=None, keyobject=None):
        self.uri = uri
        self.duration = duration
        self.title = title
        self.base_uri = base_uri
        self.byterange = byterange
        self.program_date_time = program_date_time
        self.discontinuity = discontinuity
        self.cue_out = cue_out
        self.scte35 = scte35
        self.scte35_duration = scte35_duration
        self.key = keyobject
        # Key(base_uri=base_uri, **key) if key else None

    def dumps(self, last_segment):
        output = []
        if last_segment and self.key != last_segment.key:
            output.append(str(self.key))
            output.append('\n')
        else:
            # The key must be checked anyway now for the first segment
            if self.key and last_segment is None:
                output.append(str(self.key))
                output.append('\n')

        if self.discontinuity:
            output.append('#EXT-X-DISCONTINUITY\n')
            if self.program_date_time:
                output.append('#EXT-X-PROGRAM-DATE-TIME:%s\n' %
                              format_date_time(self.program_date_time))
        if self.cue_out:
            output.append('#EXT-X-CUE-OUT-CONT\n')
        output.append('#EXTINF:%s,' % int_or_float_to_string(self.duration))
        if self.title:
            output.append(quoted(self.title))

        output.append('\n')

        if self.byterange:
            output.append('#EXT-X-BYTERANGE:%s\n' % self.byterange)

        output.append(self.uri)

        return ''.join(output)

    def __str__(self):
        return self.dumps(None)


class SegmentList(list, GroupedBasePathMixin):

    def __str__(self):
        output = []
        last_segment = None
        for segment in self:
            output.append(segment.dumps(last_segment))
            last_segment = segment
        return '\n'.join(output)

    @property
    def uri(self):
        return [seg.uri for seg in self]


    def by_key(self, key):
        return [ segment for segment in self if segment.key == key ]



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

    def __init__(self, method, base_uri, uri=None, iv=None, keyformat=None, keyformatversions=None):
        self.method = method
        self.uri = uri
        self.iv = iv
        self.keyformat = keyformat
        self.keyformatversions = keyformatversions
        self.base_uri = base_uri

    def __str__(self):
        output = [
            'METHOD=%s' % self.method,
        ]
        if self.uri:
            output.append('URI="%s"' % self.uri)
        if self.iv:
            output.append('IV=%s' % self.iv)
        if self.keyformat:
            output.append('KEYFORMAT="%s"' % self.keyformat)
        if self.keyformatversions:
            output.append('KEYFORMATVERSIONS="%s"' % self.keyformatversions)

        return '#EXT-X-KEY:' + ','.join(output)

    def __eq__(self, other):
        if not other:
            return False
        return self.method == other.method and \
            self.uri == other.uri and \
            self.iv == other.iv and \
            self.base_uri == other.base_uri and \
            self.keyformat == other.keyformat and \
            self.keyformatversions == other.keyformatversions

    def __ne__(self, other):
        return not self.__eq__(other)


class Playlist(BasePathMixin):
    '''
    Playlist object representing a link to a variant M3U8 with a specific bitrate.

    Attributes:

    `stream_info` is a named tuple containing the attributes: `program_id`,
    `bandwidth`, `average_bandwidth`, `resolution`, `codecs` and `resolution`
    which is a a tuple (w, h) of integers

    `media` is a list of related Media entries.

    More info: http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.10
    '''

    def __init__(self, uri, stream_info, media, base_uri):
        self.uri = uri
        self.base_uri = base_uri

        resolution = stream_info.get('resolution')
        if resolution != None:
            resolution = resolution.strip('"')
            values = resolution.split('x')
            resolution_pair = (int(values[0]), int(values[1]))
        else:
            resolution_pair = None

        self.stream_info = StreamInfo(
            bandwidth=stream_info['bandwidth'],
            video=stream_info.get('video'),
            audio=stream_info.get('audio'),
            subtitles=stream_info.get('subtitles'),
            closed_captions=stream_info.get('closed_captions'),
            average_bandwidth=stream_info.get('average_bandwidth'),
            program_id=stream_info.get('program_id'),
            resolution=resolution_pair,
            codecs=stream_info.get('codecs')
        )
        self.media = []
        for media_type in ('audio', 'video', 'subtitles'):
            group_id = stream_info.get(media_type)
            if not group_id:
                continue

            self.media += filter(lambda m: m.group_id == group_id, media)

    def __str__(self):
        stream_inf = []
        if self.stream_info.program_id:
            stream_inf.append('PROGRAM-ID=%d' % self.stream_info.program_id)
        if self.stream_info.closed_captions:
            stream_inf.append('CLOSED-CAPTIONS=%s' % self.stream_info.closed_captions)
        if self.stream_info.bandwidth:
            stream_inf.append('BANDWIDTH=%d' % self.stream_info.bandwidth)
        if self.stream_info.average_bandwidth:
            stream_inf.append('AVERAGE-BANDWIDTH=%d' %
                              self.stream_info.average_bandwidth)
        if self.stream_info.resolution:
            res = str(self.stream_info.resolution[
                      0]) + 'x' + str(self.stream_info.resolution[1])
            stream_inf.append('RESOLUTION=' + res)
        if self.stream_info.codecs:
            stream_inf.append('CODECS=' + quoted(self.stream_info.codecs))

        media_types = []
        for media in self.media:
            if media.type in media_types:
                continue
            else:
                media_types += [media.type]
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
            video=iframe_stream_info.get('video'),
            # Audio, subtitles, and closed captions should not exist in
            # EXT-X-I-FRAME-STREAM-INF, so just hardcode them to None.
            audio=None,
            subtitles=None,
            closed_captions=None,
            average_bandwidth=None,
            program_id=iframe_stream_info.get('program_id'),
            resolution=resolution_pair,
            codecs=iframe_stream_info.get('codecs')
        )

    def __str__(self):
        iframe_stream_inf = []
        if self.iframe_stream_info.program_id:
            iframe_stream_inf.append('PROGRAM-ID=%d' %
                                     self.iframe_stream_info.program_id)
        if self.iframe_stream_info.bandwidth:
            iframe_stream_inf.append('BANDWIDTH=%d' %
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

StreamInfo = namedtuple(
    'StreamInfo',
    ['bandwidth', 'closed_captions', 'average_bandwidth', 'program_id', 'resolution', 'codecs', 'audio', 'video', 'subtitles']
)


class Media(BasePathMixin):
    '''
    A media object from a M3U8 playlist
    https://tools.ietf.org/html/draft-pantos-http-live-streaming-16#section-4.3.4.1

    `uri`
      a string with the media uri

    `type`
    `group_id`
    `language`
    `assoc-language`
    `name`
    `default`
    `autoselect`
    `forced`
    `instream_id`
    `characteristics`
      attributes in the EXT-MEDIA tag

    `base_uri`
      uri the media comes from in URI hierarchy. ex.: http://example.com/path/to
    '''

    def __init__(self, uri=None, type=None, group_id=None, language=None,
                 name=None, default=None, autoselect=None, forced=None,
                 characteristics=None, assoc_language=None,
                 instream_id=None, base_uri=None, **extras):
        self.base_uri = base_uri
        self.uri = uri
        self.type = type
        self.group_id = group_id
        self.language = language
        self.name = name
        self.default = default
        self.autoselect = autoselect
        self.forced = forced
        self.assoc_language = assoc_language
        self.instream_id = instream_id
        self.characteristics = characteristics
        self.extras = extras

    def dumps(self):
        media_out = []

        if self.uri:
            media_out.append('URI=' + quoted(self.uri))
        if self.type:
            media_out.append('TYPE=' + self.type)
        if self.group_id:
            media_out.append('GROUP-ID=' + quoted(self.group_id))
        if self.language:
            media_out.append('LANGUAGE=' + quoted(self.language))
        if self.assoc_language:
            media_out.append('ASSOC-LANGUAGE=' + quoted(self.assoc_language))
        if self.name:
            media_out.append('NAME=' + quoted(self.name))
        if self.default:
            media_out.append('DEFAULT=' + self.default)
        if self.autoselect:
            media_out.append('AUTOSELECT=' + self.autoselect)
        if self.forced:
            media_out.append('FORCED=' + self.forced)
        if self.instream_id:
            media_out.append('INSTREAM-ID=' + self.instream_id)
        if self.characteristics:
            media_out.append('CHARACTERISTICS=' + quoted(self.characteristics))

        return ('#EXT-X-MEDIA:' + ','.join(media_out))

    def __str__(self):
        return self.dumps()


class MediaList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(playlist) for playlist in self]
        return '\n'.join(output)

    @property
    def uri(self):
        return [media.uri for media in self]


class PlaylistList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(playlist) for playlist in self]
        return '\n'.join(output)


class Start(object):

    def __init__(self, time_offset, precise=None):
        self.time_offset = float(time_offset)
        self.precise = precise

    def __str__(self):
        output = [
            'TIME-OFFSET=' + str(self.time_offset)
        ]
        if self.precise and self.precise in ['YES', 'NO']:
            output.append('PRECISE=' + str(self.precise))

        return ext_x_start + ':' + ','.join(output)


def find_key(keydata, keylist):
    if not keydata:
        return None
    for key in keylist:
        if key:
            # Check the intersection of keys and values
            if keydata.get('uri', None) == key.uri and \
               keydata.get('method', 'NONE') == key.method and \
               keydata.get('iv', None) == key.iv:
                return key
    raise KeyError("No key found for key data")


def denormalize_attribute(attribute):
    return attribute.replace('_', '-').upper()


def quoted(string):
    return '"%s"' % string


def int_or_float_to_string(number):
    return str(int(number)) if number == math.floor(number) else str(number)
