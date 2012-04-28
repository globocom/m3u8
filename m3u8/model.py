
class M3U8(object):
    '''
    Represents a single M3U8 file
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
        pass

    def dump(self, filename):
        '''
        Saves the current m3u8 to ``filename``
        '''
        pass

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
    def key(self):
        '''
        Returns a namedtuple 'Key' used to encrypt the chunks (EXT-X-KEY)

        0 - method
          is a string. ex.: "AES-128"

        1 - uri
          is a string. ex:: "https://priv.example.com/key.php?r=52"

        2 - iv
          initialization vector. a string representing a hexadecimal number. ex.: 0X12A

        '''
        return None

    @property
    def chunks(self):
        '''
        Returns an iterable with all .ts chunks from playlist, in order.
        '''
        return self.data.get('chunks', [])

    @property
    def files(self):
        '''
        Returns an iterable with all files from playlist, in order. This includes
        chunks and key uri, if present.
        '''
        return ()
