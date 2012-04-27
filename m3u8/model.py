
class M3U8(object):

    def __init__(self, content):
        pass

    def __unicode__(self):
        return self.dumps()

    def dumps(self):
        '''
        Returns the current m3u8 as a string
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
        '''
        return None

    @property
    def media_sequence(self):
        '''
        Returns the EXT-X-MEDIA-SEQUENCE as an integer
        '''
        return None

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
        return ()

    @property
    def files(self):
        '''
        Returns an iterable with all files from playlist, in order. This includes
        chunks and key uri, if present.
        '''
        return ()
