'''
M3U8 parser.

The API is the function ``parse()``. The parser classes API could change
in the future.

'''

def parse(content):
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    return Parser().parse(content)


class Parser(object):

    ext_x_targetduration = '#EXT-X-TARGETDURATION'
    ext_x_media_sequence = '#EXT-X-MEDIA-SEQUENCE'
    ext_x_key = '#EXT-X-KEY'
    extinf = '#EXTINF'

    def parse(self, content):
        data = {}
        content = content.strip()

        expect_extinf = False

        for line in content.split('\n'):

            if expect_extinf:
                self._parse_ts_chuck(line, data)
                expect_extinf = False

            elif line.startswith(self.ext_x_targetduration):
                self._parse_targetduration(line, data)

            elif line.startswith(self.ext_x_media_sequence):
                self._parse_media_sequence(line, data)

            elif line.startswith(self.ext_x_key):
                self._parse_key(line, data)

            elif line.startswith(self.extinf):
                expect_extinf = True

        return data

    def _parse_targetduration(self, line, data):
        duration = line.replace(self.ext_x_targetduration + ':', '')
        data['targetduration'] = int(duration)

    def _parse_media_sequence(self, line, data):
        seq = line.replace(self.ext_x_media_sequence + ':', '')
        data['media_sequence'] = int(seq)

    def _parse_key(self, line, data):
        params = line.replace(self.ext_x_key + ':', '').split(',')
        data['key'] = {}
        for param in params:
            name, value = param.split('=', 1)
            data['key'][name.lower()] = remove_quotes(value)

    def _parse_ts_chuck(self, line, data):
        data.setdefault('chunks', [])
        data['chunks'].append(line)


def remove_quotes(string):
    '''
    Remove quotes from string.

    Ex.:
      "foo" -> foo
      'foo' -> foo
      'foo  -> 'foo

    '''
    quotes = ('"', "'")
    if string[0] in quotes and string[-1] in quotes:
        return string[1:-1]
    return string
