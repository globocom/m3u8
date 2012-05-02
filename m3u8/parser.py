'''
M3U8 parser.


'''

ext_x_targetduration = '#EXT-X-TARGETDURATION'
ext_x_media_sequence = '#EXT-X-MEDIA-SEQUENCE'
ext_x_key = '#EXT-X-KEY'
extinf = '#EXTINF'


def parse(content):
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    data = {'chunks': []}
    next_chuck_duration = None

    for line in string_to_lines(content):

        if next_chuck_duration:
            _parse_ts_chuck(line, data, next_chuck_duration)
            next_chuck_duration = None

        elif line.startswith(ext_x_targetduration):
            _parse_targetduration(line, data)

        elif line.startswith(ext_x_media_sequence):
            _parse_media_sequence(line, data)

        elif line.startswith(ext_x_key):
            _parse_key(line, data)

        elif line.startswith(extinf):
            next_chuck_duration = _parse_duration(line)

    return data


def _parse_targetduration(line, data):
    duration = line.replace(ext_x_targetduration + ':', '')
    data['targetduration'] = int(duration)

def _parse_media_sequence(line, data):
    seq = line.replace(ext_x_media_sequence + ':', '')
    data['media_sequence'] = int(seq)

def _parse_key(line, data):
    params = line.replace(ext_x_key + ':', '').split(',')
    data['key'] = {}
    for param in params:
        name, value = param.split('=', 1)
        data['key'][name.lower()] = remove_quotes(value)

def _parse_duration(line):
    return int(line.replace(extinf + ':', '').split(',')[0])

def _parse_ts_chuck(line, data, duration=None):
    data['chunks'].append({'duration': duration,
                           'title': line})

def string_to_lines(string):
    return string.strip().split('\n')

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
