# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import iso8601
import datetime
import itertools
import re
from m3u8 import protocol

'''
http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.2
http://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
'''
ATTRIBUTELISTPATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')


def cast_date_time(value):
    return iso8601.parse_date(value)


def format_date_time(value):
    return value.isoformat()



class ParseError(Exception):

    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line

    def __str__(self):
        return 'Syntax error in manifest on line %d: %s' % (self.lineno, self.line)



def parse(content, strict=False):
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    data = {
        'media_sequence': 0,
        'is_variant': False,
        'is_endlist': False,
        'is_i_frames_only': False,
        'is_independent_segments': False,
        'playlist_type': None,
        'playlists': [],
        'segments': [],
        'iframe_playlists': [],
        'media': [],
        'keys': []
    }

    state = {
        'expect_segment': False,
        'expect_playlist': False,
        'current_key': None,
    }

    lineno = 0
    for line in string_to_lines(content):
        lineno += 1
        line = line.strip()

        if line.startswith(protocol.ext_x_byterange):
            _parse_byterange(line, state)
            state['expect_segment'] = True

        elif line.startswith(protocol.ext_x_targetduration):
            _parse_simple_parameter(line, data, float)

        elif line.startswith(protocol.ext_x_media_sequence):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_discontinuity_sequence):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_program_date_time):
            _, program_date_time = _parse_simple_parameter_raw_value(line, cast_date_time)
            if not data.get('program_date_time'):
                data['program_date_time'] = program_date_time
            state['current_program_date_time'] = program_date_time

        elif line.startswith(protocol.ext_x_discontinuity):
            state['discontinuity'] = True

        elif line.startswith(protocol.ext_x_cue_out):
            _parse_cueout(line, state)
            state['cue_out'] = True
            state['cue_start'] = True

        elif line.startswith(protocol.ext_x_cue_out_start):
            _parse_cueout_start(line, state, string_to_lines(content)[lineno - 2])
            state['cue_out'] = True
            state['cue_start'] = True

        elif line.startswith(protocol.ext_x_cue_span):
            state['cue_out'] = True
            state['cue_start'] = True

        elif line.startswith(protocol.ext_x_version):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_x_allow_cache):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_x_key):
            key = _parse_key(line)
            state['current_key'] = key
            if key not in data['keys']:
                data['keys'].append(key)

        elif line.startswith(protocol.extinf):
            _parse_extinf(line, data, state, lineno, strict)
            state['expect_segment'] = True

        elif line.startswith(protocol.ext_x_stream_inf):
            state['expect_playlist'] = True
            _parse_stream_inf(line, data, state)

        elif line.startswith(protocol.ext_x_i_frame_stream_inf):
            _parse_i_frame_stream_inf(line, data)

        elif line.startswith(protocol.ext_x_media):
            _parse_media(line, data, state)

        elif line.startswith(protocol.ext_x_playlist_type):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_i_frames_only):
            data['is_i_frames_only'] = True

        elif line.startswith(protocol.ext_is_independent_segments):
            data['is_independent_segments'] = True

        elif line.startswith(protocol.ext_x_endlist):
            data['is_endlist'] = True

        elif line.startswith(protocol.ext_x_map):
            quoted_parser = remove_quotes_parser('uri')
            segment_map_info = _parse_attribute_list(protocol.ext_x_map, line, quoted_parser)
            data['segment_map'] = segment_map_info

        elif line.startswith(protocol.ext_x_start):
            attribute_parser = {
                "time_offset": lambda x: float(x)
            }
            start_info = _parse_attribute_list(protocol.ext_x_start, line, attribute_parser)
            data['start'] = start_info

        # Comments and whitespace
        elif line.startswith('#'):
            # comment
            pass

        elif line.strip() == '':
            # blank lines are legal
            pass

        elif state['expect_segment']:
            _parse_ts_chunk(line, data, state)
            state['expect_segment'] = False

        elif state['expect_playlist']:
            _parse_variant_playlist(line, data, state)
            state['expect_playlist'] = False

        elif strict:
            raise ParseError(lineno, line)

    return data


def _parse_key(line):
    params = ATTRIBUTELISTPATTERN.split(line.replace(protocol.ext_x_key + ':', ''))[1::2]
    key = {}
    for param in params:
        name, value = param.split('=', 1)
        key[normalize_attribute(name)] = remove_quotes(value)
    return key


def _parse_extinf(line, data, state, lineno, strict):
    chunks = line.replace(protocol.extinf + ':', '').split(',', 1)
    if len(chunks) == 2:
        duration, title = chunks
    elif len(chunks) == 1:
        if strict:
            raise ParseError(lineno, line)
        else:
            duration = chunks[0]
            title = ''
    if 'segment' not in state:
        state['segment'] = {}
    state['segment']['duration'] = float(duration)
    state['segment']['title'] = remove_quotes(title)


def _parse_ts_chunk(line, data, state):
    segment = state.pop('segment')
    if state.get('current_program_date_time'):
        segment['program_date_time'] = state['current_program_date_time']
        state['current_program_date_time'] += datetime.timedelta(seconds=segment['duration'])
    segment['uri'] = line
    segment['cue_out'] = state.pop('cue_out', False)
    if state.get('current_cue_out_scte35'):
        segment['scte35'] = state['current_cue_out_scte35']
        segment['scte35_duration'] = state['current_cue_out_duration']
    segment['discontinuity'] = state.pop('discontinuity', False)
    if state.get('current_key'):
        segment['key'] = state['current_key']
    else:
        # For unencrypted segments, the initial key would be None
        if None not in data['keys']:
            data['keys'].append(None)
    data['segments'].append(segment)


def _parse_attribute_list(prefix, line, atribute_parser):
    params = ATTRIBUTELISTPATTERN.split(line.replace(prefix + ':', ''))[1::2]

    attributes = {}
    for param in params:
        name, value = param.split('=', 1)
        name = normalize_attribute(name)

        if name in atribute_parser:
            value = atribute_parser[name](value)

        attributes[name] = value

    return attributes

def _parse_stream_inf(line, data, state):
    data['is_variant'] = True
    data['media_sequence'] = None
    atribute_parser = remove_quotes_parser('codecs', 'audio', 'video', 'subtitles', 'closed_captions')
    atribute_parser["program_id"] = int
    atribute_parser["bandwidth"] = lambda x: int(float(x))
    atribute_parser["average_bandwidth"] = int
    state['stream_info'] = _parse_attribute_list(protocol.ext_x_stream_inf, line, atribute_parser)


def _parse_i_frame_stream_inf(line, data):
    atribute_parser = remove_quotes_parser('codecs', 'uri')
    atribute_parser["program_id"] = int
    atribute_parser["bandwidth"] = int
    iframe_stream_info = _parse_attribute_list(protocol.ext_x_i_frame_stream_inf, line, atribute_parser)
    iframe_playlist = {'uri': iframe_stream_info.pop('uri'),
                       'iframe_stream_info': iframe_stream_info}

    data['iframe_playlists'].append(iframe_playlist)


def _parse_media(line, data, state):
    quoted = remove_quotes_parser('uri', 'group_id', 'language', 'name', 'characteristics')
    media = _parse_attribute_list(protocol.ext_x_media, line, quoted)
    data['media'].append(media)


def _parse_variant_playlist(line, data, state):
    playlist = {'uri': line,
                'stream_info': state.pop('stream_info')}

    data['playlists'].append(playlist)


def _parse_byterange(line, state):
    if 'segment' not in state:
        state['segment'] = {}
    state['segment']['byterange'] = line.replace(protocol.ext_x_byterange + ':', '')


def _parse_simple_parameter_raw_value(line, cast_to=str, normalize=False):
    param, value = line.split(':', 1)
    param = normalize_attribute(param.replace('#EXT-X-', ''))
    if normalize:
        value = normalize_attribute(value)
    return param, cast_to(value)


def _parse_and_set_simple_parameter_raw_value(line, data, cast_to=str, normalize=False):
    param, value = _parse_simple_parameter_raw_value(line, cast_to, normalize)
    data[param] = value
    return data[param]


def _parse_simple_parameter(line, data, cast_to=str):
    return _parse_and_set_simple_parameter_raw_value(line, data, cast_to, True)


def _parse_cueout(line, state):
    param, value = line.split(':', 1)
    res = re.match('.*Duration=(.*),SCTE35=(.*)$', value)
    if res:
        state['current_cue_out_duration'] = res.group(1)
        state['current_cue_out_scte35'] = res.group(2)

def _cueout_elemental(line, state, prevline):
    param, value = line.split(':', 1)
    res = re.match('.*EXT-OATCLS-SCTE35:(.*)$', prevline)
    if res:
        return (res.group(1), value)
    else:
        return None

def _cueout_envivio(line, state, prevline):
    param, value = line.split(':', 1)
    res = re.match('.*DURATION=(.*),.*,CUE="(.*)"', value)
    if res:
        return (res.group(2), res.group(1))
    else:
        return None

def _parse_cueout_start(line, state, prevline):
    _cueout_state = _cueout_elemental(line, state, prevline) or _cueout_envivio(line, state, prevline)
    if _cueout_state:
        state['current_cue_out_scte35'] = _cueout_state[0]
        state['current_cue_out_duration'] = _cueout_state[1]


def string_to_lines(string):
    return string.strip().splitlines()


def remove_quotes_parser(*attrs):
    return dict(zip(attrs, itertools.repeat(remove_quotes)))


def remove_quotes(string):
    '''
    Remove quotes from string.

    Ex.:
      "foo" -> foo
      'foo' -> foo
      'foo  -> 'foo

    '''
    quotes = ('"', "'")
    if string.startswith(quotes) and string.endswith(quotes):
        return string[1:-1]
    return string


def normalize_attribute(attribute):
    return attribute.replace('-', '_').lower().strip()


def is_url(uri):
    return uri.startswith(('https://', 'http://'))

