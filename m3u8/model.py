# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import os
import errno
import math

from m3u8.protocol import ext_x_start, ext_x_key, ext_x_session_key
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

     `session_keys`
       Returns the list of `SessionKey` objects used to encrypt multiple segments from m3u8.

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

    def __init__(self, content=None, base_path=None, base_uri=None, strict=False, custom_tags_parser=None):
        if content is not None:
            self.data = parse(content, strict, custom_tags_parser)
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

        server_control = self.data.get('server_control', None)
        self.server_control = server_control and ServerControl(**server_control)

        part_inf = self.data.get('part_inf', None)
        self.part_inf = part_inf and PartInformation(**part_inf)

        skip = self.data.get('skip', None)
        self.skip = skip and Skip(**skip)

        self.rendition_reports = RenditionReportList([ RenditionReport(base_uri=self.base_uri, **rendition_report)
                                                  for rendition_report in self.data.get('rendition_reports', []) ])

        self.session_data = SessionDataList([ SessionData(**session_data)
                             for session_data in self.data.get('session_data', [])
                             if 'data_id' in session_data ])

        self.session_keys = [ SessionKey(base_uri=self.base_uri, **params) if params else None
                      for params in self.data.get('session_keys', []) ]

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
        for key in self.session_keys:
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
        for key in self.session_keys:
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

    def add_rendition_report(self, report):
        self.rendition_reports.append(report)

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
            output.append('#EXT-X-VERSION:' + str(self.version))
        if self.target_duration:
            output.append('#EXT-X-TARGETDURATION:' +
                          int_or_float_to_string(self.target_duration))
        if not (self.playlist_type is None or self.playlist_type == ''):
            output.append('#EXT-X-PLAYLIST-TYPE:%s' % str(self.playlist_type).upper())
        if self.start:
            output.append(str(self.start))
        if self.is_i_frames_only:
            output.append('#EXT-X-I-FRAMES-ONLY')
        if self.segment_map:
            map_output = []
            if self.segment_map.get('uri'):
                map_output.append('URI=' + quoted(self.segment_map['uri']))
            if self.segment_map.get('byterange'):
                map_output.append('BYTERANGE=' + self.segment_map['byterange'])
            output.append('#EXT-X-MAP:' + ','.join(map_output))
        if self.server_control:
            output.append(str(self.server_control))
        if self.is_variant:
            if self.media:
                output.append(str(self.media))
            output.append(str(self.playlists))
            if self.iframe_playlists:
                output.append(str(self.iframe_playlists))
        if self.part_inf:
            output.append(str(self.part_inf))
        if self.skip:
            output.append(str(self.skip))
        if self.session_data:
            output.append(str(self.session_data))

        for key in self.session_keys:
            output.append(str(key))

        output.append(str(self.segments))

        if self.rendition_reports:
            output.append(str(self.rendition_reports))

        if self.is_endlist:
            output.append('#EXT-X-ENDLIST')

        # ensure that the last line is terminated correctly
        if output[-1] and not output[-1].endswith('\n'):
            output.append('')

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
      Returns the EXT-X-PROGRAM-DATE-TIME as a datetime. This field is only set
      if EXT-X-PROGRAM-DATE-TIME exists for this segment
      http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.5

    `current_program_date_time`
      Returns a datetime of this segment, either the value of `program_date_time`
      when EXT-X-PROGRAM-DATE-TIME is set or a calculated value based on previous
      segments' EXT-X-PROGRAM-DATE-TIME and EXTINF values

    `discontinuity`
      Returns a boolean indicating if a EXT-X-DISCONTINUITY tag exists
      http://tools.ietf.org/html/draft-pantos-http-live-streaming-13#section-3.4.11

    `cue_out_start`
      Returns a boolean indicating if a EXT-X-CUE-OUT tag exists

    `cue_out`
      Returns a boolean indicating if a EXT-X-CUE-OUT-CONT tag exists
      Note: for backwards compatibility, this will be True when cue_out_start
            is True, even though this tag did not exist in the input, and
            EXT-X-CUE-OUT-CONT will not exist in the output

    `cue_in`
      Returns a boolean indicating if a EXT-X-CUE-IN tag exists

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

    `parts`
      partial segments that make up this segment
    '''

    def __init__(self, uri=None, base_uri=None, program_date_time=None, current_program_date_time=None,
                 duration=None, title=None, byterange=None, cue_out=False, cue_out_start=False,
                 cue_in=False, discontinuity=False, key=None, scte35=None, scte35_duration=None,
                 keyobject=None, parts=None):
        self.uri = uri
        self.duration = duration
        self.title = title
        self.base_uri = base_uri
        self.byterange = byterange
        self.program_date_time = program_date_time
        self.current_program_date_time = current_program_date_time
        self.discontinuity = discontinuity
        self.cue_out_start = cue_out_start
        self.cue_out = cue_out
        self.cue_in = cue_in
        self.scte35 = scte35
        self.scte35_duration = scte35_duration
        self.key = keyobject
        self.parts = PartialSegmentList( [ PartialSegment(base_uri=self.base_uri, **partial) for partial in parts ] if parts else [] )

        # Key(base_uri=base_uri, **key) if key else None

    def add_part(self, part):
        self.parts.append(part)

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

        if self.cue_out_start:
            output.append('#EXT-X-CUE-OUT{}\n'.format(
                (':' + self.scte35_duration) if self.scte35_duration else ''))
        elif self.cue_out:
            output.append('#EXT-X-CUE-OUT-CONT\n')
        if self.cue_in:
            output.append('#EXT-X-CUE-IN\n')

        if self.parts:
            output.append(str(self.parts))
            output.append('\n')

        if self.uri:
            if self.duration is not None:
                output.append('#EXTINF:%s,' % int_or_float_to_string(self.duration))
                if self.title:
                    output.append(self.title)
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



class PartialSegment(BasePathMixin):
    '''
    A partial segment from a M3U8 playlist

    `uri`
      a string with the segment uri

    `program_date_time`
      Returns the EXT-X-PROGRAM-DATE-TIME as a datetime. This field is only set
      if EXT-X-PROGRAM-DATE-TIME exists for this segment
      http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.5

    `current_program_date_time`
      Returns a datetime of this segment, either the value of `program_date_time`
      when EXT-X-PROGRAM-DATE-TIME is set or a calculated value based on previous
      segments' EXT-X-PROGRAM-DATE-TIME and EXTINF values

    `duration`
      duration attribute from EXTINF parameter

    `byterange`
      byterange attribute from EXT-X-BYTERANGE parameter

    `independent`
      the Partial Segment contains an independent frame

    `gap`
      the Partial Segment is not available
    '''

    def __init__(self, base_uri, uri, duration, program_date_time=None,
                 current_program_date_time=None, byterange=None,
                 independent=None, gap=None):
        self.base_uri = base_uri
        self.uri = uri
        self.duration = duration
        self.program_date_time = program_date_time
        self.current_program_date_time = current_program_date_time
        self.byterange = byterange
        self.independent = independent
        self.gap = gap

    def dumps(self, last_segment):
        output = ['#EXT-X-PART:DURATION=%s,URI="%s"' % (
            int_or_float_to_string(self.duration), self.uri
        )]

        if self.independent:
            output.append(',INDEPENDENT=%s' % self.independent)

        if self.byterange:
            output.append(',BYTERANGE=%s' % self.byterange)

        if self.gap:
            output.append(',GAP=%s' % self.gap)

        return ''.join(output)

    def __str__(self):
        return self.dumps(None)

class PartialSegmentList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(part) for part in self]
        return '\n'.join(output)

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

    tag = ext_x_key

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

        return self.tag + ':' + ','.join(output)

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

class SessionKey(Key):
    tag = ext_x_session_key

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
            codecs=stream_info.get('codecs'),
            frame_rate=stream_info.get('frame_rate')
        )
        self.media = []
        for media_type in ('audio', 'video', 'subtitles'):
            group_id = stream_info.get(media_type)
            if not group_id:
                continue

            self.media += filter(lambda m: m.group_id == group_id, media)

    def __str__(self):
        media_types = []
        stream_inf = [str(self.stream_info)]
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
            codecs=iframe_stream_info.get('codecs'),
            frame_rate=None
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


class StreamInfo(object):
    bandwidth = None
    closed_captions = None
    average_bandwidth = None
    program_id = None
    resolution = None
    codecs = None
    audio = None
    video = None
    subtitles = None
    frame_rate = None

    def __init__(self, **kwargs):
        self.bandwidth = kwargs.get("bandwidth")
        self.closed_captions = kwargs.get("closed_captions")
        self.average_bandwidth = kwargs.get("average_bandwidth")
        self.program_id = kwargs.get("program_id")
        self.resolution = kwargs.get("resolution")
        self.codecs = kwargs.get("codecs")
        self.audio = kwargs.get("audio")
        self.video = kwargs.get("video")
        self.subtitles = kwargs.get("subtitles")
        self.frame_rate = kwargs.get("frame_rate")

    def __str__(self):
        stream_inf = []
        if self.program_id is not None:
            stream_inf.append('PROGRAM-ID=%d' % self.program_id)
        if self.closed_captions is not None:
            stream_inf.append('CLOSED-CAPTIONS=%s' % self.closed_captions)
        if self.bandwidth is not None:
            stream_inf.append('BANDWIDTH=%d' % self.bandwidth)
        if self.average_bandwidth is not None:
            stream_inf.append('AVERAGE-BANDWIDTH=%d' %
                              self.average_bandwidth)
        if self.resolution is not None:
            res = str(self.resolution[
                      0]) + 'x' + str(self.resolution[1])
            stream_inf.append('RESOLUTION=' + res)
        if self.frame_rate is not None:
            stream_inf.append('FRAME-RATE=%.5g' % self.frame_rate)
        if self.codecs is not None:
            stream_inf.append('CODECS=' + quoted(self.codecs))
        return ",".join(stream_inf)


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
            media_out.append('INSTREAM-ID=' + quoted(self.instream_id))
        if self.characteristics:
            media_out.append('CHARACTERISTICS=' + quoted(self.characteristics))

        return ('#EXT-X-MEDIA:' + ','.join(media_out))

    def __str__(self):
        return self.dumps()


class TagList(list):

    def __str__(self):
        output = [str(tag) for tag in self]
        return '\n'.join(output)


class MediaList(TagList, GroupedBasePathMixin):

    @property
    def uri(self):
        return [media.uri for media in self]


class PlaylistList(TagList, GroupedBasePathMixin):
    pass


class SessionDataList(TagList):
    pass


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

class RenditionReport(BasePathMixin):
    def __init__(self, base_uri, uri, last_msn, last_part=None):
        self.base_uri = base_uri
        self.uri = uri
        self.last_msn = last_msn
        self.last_part = last_part

    def dumps(self):
        report = []
        report.append('URI=' + quoted(self.uri))
        report.append('LAST-MSN=' + int_or_float_to_string(self.last_msn))
        if self.last_part is not None:
            report.append('LAST-PART=' + int_or_float_to_string(
                self.last_part))

        return ('#EXT-X-RENDITION-REPORT:' + ','.join(report))

    def __str__(self):
        return self.dumps()

class RenditionReportList(list, GroupedBasePathMixin):

    def __str__(self):
        output = [str(report) for report in self]
        return '\n'.join(output)

class ServerControl(object):
    def __init__(self, can_skip_until=None, can_block_reload=None,
                 hold_back=None, part_hold_back=None):
        self.can_skip_until = can_skip_until
        self.can_block_reload = can_block_reload
        self.hold_back = hold_back
        self.part_hold_back = part_hold_back

    def __getitem__(self, item):
        return getattr(self, item)

    def dumps(self):
        ctrl = []
        if self.can_block_reload:
            ctrl.append('CAN-BLOCK-RELOAD=%s' % self.can_block_reload)
        for attr in ['hold_back', 'part_hold_back', 'can_skip_until']:
            if self[attr]:
                ctrl.append('%s=%s' % (
                    denormalize_attribute(attr),
                    int_or_float_to_string(self[attr])
                ))

        return '#EXT-X-SERVER-CONTROL:' + ','.join(ctrl)

    def __str__(self):
        return self.dumps()

class Skip(object):
    def __init__(self, skipped_segments=None):
        self.skipped_segments = skipped_segments

    def dumps(self):
        return '#EXT-X-SKIP:SKIPPED-SEGMENTS=%s' % int_or_float_to_string(
            self.skipped_segments)

    def __str__(self):
        return self.dumps()

class PartInformation(object):
    def __init__(self, part_target=None):
        self.part_target = part_target

    def dumps(self):
        return '#EXT-X-PART-INF:PART-TARGET=%s' % int_or_float_to_string(
            self.part_target)

    def __str__(self):
        return self.dumps()

class SessionData(object):
    def __init__(self, data_id, value=None, uri=None, language=None):
        self.data_id = data_id
        self.value = value
        self.uri = uri
        self.language = language

    def dumps(self):
        session_data_out = ['DATA-ID=' + quoted(self.data_id)]

        if self.value:
            session_data_out.append('VALUE=' + quoted(self.value))
        elif self.uri:
            session_data_out.append('URI=' + quoted(self.uri))
        if self.language:
            session_data_out.append('LANGUAGE=' + quoted(self.language))

        return '#EXT-X-SESSION-DATA:' + ','.join(session_data_out)

    def __str__(self):
        return self.dumps()

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
