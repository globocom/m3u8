import os
import errno
from collections import namedtuple

from m3u8 import parser

class M3U8(object):
    '''
    Represents a single M3U8 playlist. Should be instantiated with
    the content as string.
    '''

    def __init__(self, content):
        self.data = parser.parse(content)

    def __unicode__(self):
        return self.dumps()

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
            output.append(self.key_as_string)
        if self.target_duration:
            output.append('#EXT-X-TARGETDURATION:' + str(self.target_duration))

        for segment in self.segments:
            extinf = '#EXTINF:%s,' % segment.duration
            if segment.title:
                extinf += '"%s"' % segment.title
            output.append(''.join(extinf))
            output.append(segment.uri)

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

    @property
    def is_variant(self):
        '''
        Returns true if this M3U8 is a variant playlist, with links to
        other M3U8s with different bitrates.

        If true, `playlists` if a list of the playlists available.

        '''
        return self.data.get('is_variant', False)

    @property
    def target_duration(self):
        '''
        Returns the EXT-X-TARGETDURATION as an integer
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.2
        '''
        return self.data.get('targetduration')

    @property
    def media_sequence(self):
        '''
        Returns the EXT-X-MEDIA-SEQUENCE as an integer
        http://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-3.3.3
        '''
        return self.data.get('media_sequence')

    @property
    def version(self):
        '''
        Return the EXT-X-VERSION as is
        '''
        return self.data.get('version')

    @property
    def allow_cache(self):
        '''
        Return the EXT-X-ALLOW-CACHE as is
        '''
        return self.data.get('allow_cache')

    @property
    def key(self):
        '''
        Returns a namedtuple 'Key' used to encrypt the segments (EXT-X-KEY)

        `method`
          is a string. ex.: "AES-128"

        `uri`
          is a string. ex:: "https://priv.example.com/key.php?r=52"

        `iv`
          initialization vector. a string representing a hexadecimal number. ex.: 0X12A

        '''
        if 'key' not in self.data:
            return None

        Key = namedtuple('Key', ['method', 'uri', 'iv'])
        return Key(method=self.data['key']['method'],
                   uri=self.data['key']['uri'],
                   iv=self.data['key'].get('iv'))

    @property
    def key_as_string(self):
        if not self.key:
            return ''

        output = [
            'METHOD=%s' % self.key.method,
            'URI="%s"' % self.key.uri,
            ]

        if self.key.iv:
            output.append('IV=%s' % self.key.iv)

        return '#EXT-X-KEY:' + ','.join(output)

    @property
    def segments(self):
        '''
        Returns an iterable with all .ts segments from playlist, in order.
        Each segment is a namedtuple `Segment` with the attributes

        `uri`
          a string with the segment uri

        `title`
          title attribute from EXTINF parameter

        `duration`
          duration attribute from EXTINF paramter

        '''
        Segment = namedtuple('Segment', ['uri', 'title', 'duration'])

        segments = []
        for segment in self.data['segments']:
            segments.append(Segment(uri=segment['uri'],
                                    title=segment.get('title'),
                                    duration=segment.get('duration')))

        return segments

    @property
    def files(self):
        '''
        Returns an iterable with all files from playlist, in order. This includes
        segments and key uri, if present.
        '''
        return ()

    @property
    def playlists(self):
        '''
        If this is a variant playlist (`is_variant` is True), returns a list of
        Playlist objects, each one representing a link to another M3U8 with
        a specific bitrate.

        Each object in the list has the following attributes:

        `resource`
          url to the m3u8

        `stream_info`
          object with all attributes from EXT-X-STREAM-INF (`program_id`, `bandwidth` and `codecs`)

        '''
        Playlist = namedtuple('Playlist', ['resource', 'stream_info'])
        StreamInfo = namedtuple('StreamInfo', ['bandwidth', 'program_id', 'codecs'])

        playlists = []
        for playlist in self.data.get('playlists', []):
            stream_info = StreamInfo(bandwidth = playlist['stream_info']['bandwidth'],
                                     program_id = playlist['stream_info'].get('program_id'),
                                     codecs = playlist['stream_info'].get('codecs'))
            playlists.append(Playlist(resource = playlist['resource'],
                                      stream_info = stream_info))

        return playlists

def denormalize_attribute(attribute):
    return attribute.replace('_','-').upper()
