'''
M3U8 parser.

'''

from collections import namedtuple

ext_x_targetduration = '#EXT-X-TARGETDURATION'
ext_x_media_sequence = '#EXT-X-MEDIA-SEQUENCE'
ext_x_key = '#EXT-X-KEY'
ext_x_stream_inf = '#EXT-X-STREAM-INF'
extinf = '#EXTINF'


def parse(content):
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    data = {
        'is_variant': False,
        'playlists': [],
        'chunks': [],
        }

    state = {
        'expect_segment': False,
        'expect_playlist': False,
        }

    for line in string_to_lines(content):

        if state['expect_segment']:
            _parse_ts_chuck(line, data, state)
            state['expect_segment'] = False

        elif state['expect_playlist']:
            _parse_variant_playlist(line, data, state)
            state['expect_playlist'] = False

        elif line.startswith(ext_x_targetduration):
            _parse_targetduration(line, data)

        elif line.startswith(ext_x_media_sequence):
            _parse_media_sequence(line, data)

        elif line.startswith(ext_x_key):
            _parse_key(line, data)

        elif line.startswith(extinf):
            _parse_extinf(line, data, state)
            state['expect_segment'] = True

        elif line.startswith(ext_x_stream_inf):
            state['expect_playlist'] = True
            _parse_stream_inf(line, data, state)

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

def _parse_extinf(line, data, state):
    duration, title = line.replace(extinf + ':', '').split(',')
    state['segment_info'] = {'duration': int(duration), 'title': remove_quotes(title)}

def _parse_ts_chuck(line, data, state):
    Segment = namedtuple('Segment', ['uri', 'title', 'duration'])
    info = state.pop('segment_info')

    data['chunks'].append(Segment(uri=line,
                                  title=info['title'],
                                  duration=info['duration']))

def _parse_stream_inf(line, data, state):
    params = line.replace(ext_x_stream_inf + ':', '').split(',')
    StreamInfo = namedtuple('StreamInfo', ['program_id', 'bandwidth', 'codecs'])

    tmpdata = {}
    for param in params:
        name, value = param.split('=', 1)
        tmpdata[name] = value

    codecs = tmpdata.get('CODECS')
    if codecs:
        codecs = remove_quotes(codecs)

    stream_info = StreamInfo(program_id=tmpdata.get('PROGRAM-ID'),
                             bandwidth=tmpdata.get('BANDWIDTH'),
                             codecs=codecs)


    data['is_variant'] = True
    state['stream_info'] = stream_info

def _parse_variant_playlist(line, data, state):
    VariantPlaylist = namedtuple('VariantPlaylist', ['resource', 'stream_info'])
    data['playlists'].append(VariantPlaylist(resource=line,
                                             stream_info=state.pop('stream_info')))

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
    if string and string[0] in quotes and string[-1] in quotes:
        return string[1:-1]
    return string
