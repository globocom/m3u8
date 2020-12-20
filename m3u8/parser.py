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


def parse(content, strict=False, custom_tags_parser=None):
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
        'keys': [],
        'rendition_reports': [],
        'skip': {},
        'part_inf': {},
        'session_data': [],
        'session_keys': [],
    }

    state = {
        'expect_segment': False,
        'expect_playlist': False,
        'current_key': None,
        'current_segment_map': None,
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
            state['program_date_time'] = program_date_time

        elif line.startswith(protocol.ext_x_discontinuity):
            state['discontinuity'] = True

        elif line.startswith(protocol.ext_x_cue_out_cont):
            _parse_cueout_cont(line, state)
            state['cue_out'] = True

        elif line.startswith(protocol.ext_x_cue_out):
            _parse_cueout(line, state, string_to_lines(content)[lineno - 2])
            state['cue_out_start'] = True
            state['cue_out'] = True

        elif line.startswith(protocol.ext_x_cue_in):
            state['cue_in'] = True

        elif line.startswith(protocol.ext_x_cue_span):
            state['cue_out'] = True

        elif line.startswith(protocol.ext_x_version):
            _parse_simple_parameter(line, data, int)

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
            state['current_segment_map'] = segment_map_info
            # left for backward compatibility
            data['segment_map'] = segment_map_info

        elif line.startswith(protocol.ext_x_start):
            attribute_parser = {
                "time_offset": lambda x: float(x)
            }
            start_info = _parse_attribute_list(protocol.ext_x_start, line, attribute_parser)
            data['start'] = start_info

        elif line.startswith(protocol.ext_x_server_control):
            _parse_server_control(line, data, state)

        elif line.startswith(protocol.ext_x_part_inf):
            _parse_part_inf(line, data, state)

        elif line.startswith(protocol.ext_x_rendition_report):
            _parse_rendition_report(line, data, state)

        elif line.startswith(protocol.ext_x_part):
            _parse_part(line, data, state)

        elif line.startswith(protocol.ext_x_skip):
            _parse_skip(line, data, state)

        elif line.startswith(protocol.ext_x_session_data):
            _parse_session_data(line, data, state)

        elif line.startswith(protocol.ext_x_session_key):
            _parse_session_key(line, data, state)

        elif line.startswith(protocol.ext_x_preload_hint):
            _parse_preload_hint(line, data, state)

        elif line.startswith(protocol.ext_x_daterange):
            _parse_daterange(line, data, state)

        elif line.startswith(protocol.ext_x_gap):
            state['gap'] = True

        # Comments and whitespace
        elif line.startswith('#'):
            if callable(custom_tags_parser):
                custom_tags_parser(line, data, lineno)

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

    # there could be remaining partial segments
    if 'segment' in state:
        data['segments'].append(state.pop('segment'))

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
    state['segment']['title'] = title


def _parse_ts_chunk(line, data, state):
    segment = state.pop('segment')
    if state.get('program_date_time'):
        segment['program_date_time'] = state.pop('program_date_time')
    if state.get('current_program_date_time'):
        segment['current_program_date_time'] = state['current_program_date_time']
        state['current_program_date_time'] += datetime.timedelta(seconds=segment['duration'])
    segment['uri'] = line
    segment['cue_in'] = state.pop('cue_in', False)
    segment['cue_out'] = state.pop('cue_out', False)
    segment['cue_out_start'] = state.pop('cue_out_start', False)
    if state.get('current_cue_out_scte35'):
        segment['scte35'] = state['current_cue_out_scte35']
    if state.get('current_cue_out_duration'):
        segment['scte35_duration'] = state['current_cue_out_duration']
    segment['discontinuity'] = state.pop('discontinuity', False)
    if state.get('current_key'):
        segment['key'] = state['current_key']
    else:
        # For unencrypted segments, the initial key would be None
        if None not in data['keys']:
            data['keys'].append(None)
    if state.get('current_segment_map'):
        segment['init_section'] = state['current_segment_map']
    segment['dateranges'] = state.pop('dateranges', None)
    segment['gap_tag'] = state.pop('gap', None)
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
    atribute_parser["frame_rate"] = float
    atribute_parser["video_range"] = str
    atribute_parser["hdcp_level"] = str
    state['stream_info'] = _parse_attribute_list(protocol.ext_x_stream_inf, line, atribute_parser)


def _parse_i_frame_stream_inf(line, data):
    atribute_parser = remove_quotes_parser('codecs', 'uri')
    atribute_parser["program_id"] = int
    atribute_parser["bandwidth"] = int
    atribute_parser["average_bandwidth"] = int
    atribute_parser["video_range"] = str
    atribute_parser["hdcp_level"] = str
    iframe_stream_info = _parse_attribute_list(protocol.ext_x_i_frame_stream_inf, line, atribute_parser)
    iframe_playlist = {'uri': iframe_stream_info.pop('uri'),
                       'iframe_stream_info': iframe_stream_info}

    data['iframe_playlists'].append(iframe_playlist)


def _parse_media(line, data, state):
    quoted = remove_quotes_parser('uri', 'group_id', 'language', 'assoc_language', 'name', 'instream_id', 'characteristics', 'channels')
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
        value = value.strip().lower()
    return param, cast_to(value)


def _parse_and_set_simple_parameter_raw_value(line, data, cast_to=str, normalize=False):
    param, value = _parse_simple_parameter_raw_value(line, cast_to, normalize)
    data[param] = value
    return data[param]


def _parse_simple_parameter(line, data, cast_to=str):
    return _parse_and_set_simple_parameter_raw_value(line, data, cast_to, True)


def _parse_cueout_cont(line, state):
    param, value = line.split(':', 1)
    res = re.match('.*Duration=(.*),SCTE35=(.*)$', value)
    if res:
        state['current_cue_out_duration'] = res.group(1)
        state['current_cue_out_scte35'] = res.group(2)

def _cueout_no_duration(line):
    # this needs to be called first since line.split in all other
    # parsers will throw a ValueError if passed just this tag
    if line == protocol.ext_x_cue_out:
        return (None, None)

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

def _cueout_duration(line):
    # this needs to be called after _cueout_elemental
    # as it would capture those cues incompletely
    # This was added seperately rather than modifying "simple"
    param, value = line.split(':', 1)
    res = re.match(r'DURATION=(.*)', value)
    if res:
        return (None, res.group(1))

def _cueout_simple(line):
    # this needs to be called after _cueout_elemental
    # as it would capture those cues incompletely
    param, value = line.split(':', 1)
    res = re.match(r'^(\d+(?:\.\d)?\d*)$', value)
    if res:
        return (None, res.group(1))

def _parse_cueout(line, state, prevline):
    _cueout_state = (_cueout_no_duration(line)
                     or _cueout_elemental(line, state, prevline)
                     or _cueout_envivio(line, state, prevline)
                     or _cueout_duration(line)
                     or _cueout_simple(line))
    if _cueout_state:
        state['current_cue_out_scte35'] = _cueout_state[0]
        state['current_cue_out_duration'] = _cueout_state[1]

def _parse_server_control(line, data, state):
    attribute_parser = {
        "can_block_reload":     str,
        "hold_back":            lambda x: float(x),
        "part_hold_back":       lambda x: float(x),
        "can_skip_until":       lambda x: float(x),
        "can_skip_dateranges":  str
    }

    data['server_control'] = _parse_attribute_list(
        protocol.ext_x_server_control, line, attribute_parser
    )

def _parse_part_inf(line, data, state):
    attribute_parser = {
        "part_target": lambda x: float(x)
    }

    data['part_inf'] = _parse_attribute_list(
        protocol.ext_x_part_inf, line, attribute_parser
    )

def _parse_rendition_report(line, data, state):
    attribute_parser = remove_quotes_parser('uri')
    attribute_parser['last_msn'] = int
    attribute_parser['last_part'] = int

    rendition_report = _parse_attribute_list(
        protocol.ext_x_rendition_report, line, attribute_parser
    )

    data['rendition_reports'].append(rendition_report)

def _parse_part(line, data, state):
    attribute_parser = remove_quotes_parser('uri')
    attribute_parser['duration'] = lambda x: float(x)
    attribute_parser['independent'] = str
    attribute_parser['gap'] = str
    attribute_parser['byterange'] = str

    part = _parse_attribute_list(protocol.ext_x_part, line, attribute_parser)

    # this should always be true according to spec
    if state.get('current_program_date_time'):
        part['program_date_time'] = state['current_program_date_time']
        state['current_program_date_time'] += datetime.timedelta(seconds=part['duration'])

    part['dateranges'] = state.pop('dateranges', None)
    part['gap_tag'] = state.pop('gap', None)

    if 'segment' not in state:
        state['segment'] = {}
    segment = state['segment']
    if 'parts' not in segment:
        segment['parts'] = []

    segment['parts'].append(part)

def _parse_skip(line, data, state):
    attribute_parser = remove_quotes_parser('recently_removed_dateranges')
    attribute_parser['skipped_segments'] = int

    data['skip'] = _parse_attribute_list(protocol.ext_x_skip, line, attribute_parser)

def _parse_session_data(line, data, state):
    quoted = remove_quotes_parser('data_id', 'value', 'uri', 'language')
    session_data = _parse_attribute_list(protocol.ext_x_session_data, line, quoted)
    data['session_data'].append(session_data)

def _parse_session_key(line, data, state):
    params = ATTRIBUTELISTPATTERN.split(line.replace(protocol.ext_x_session_key + ':', ''))[1::2]
    key = {}
    for param in params:
        name, value = param.split('=', 1)
        key[normalize_attribute(name)] = remove_quotes(value)
    data['session_keys'].append(key)

def _parse_preload_hint(line, data, state):
    attribute_parser = remove_quotes_parser('uri')
    attribute_parser['type'] = str
    attribute_parser['byterange_start'] = int
    attribute_parser['byterange_length'] = int

    data['preload_hint'] = _parse_attribute_list(
        protocol.ext_x_preload_hint, line, attribute_parser
    )

def _parse_daterange(line, date, state):
    attribute_parser = remove_quotes_parser('id', 'class', 'start_date', 'end_date')
    attribute_parser['duration'] = float
    attribute_parser['planned_duration'] = float
    attribute_parser['end_on_next'] = str
    attribute_parser['scte35_cmd'] = str
    attribute_parser['scte35_out'] = str
    attribute_parser['scte35_in'] = str

    parsed = _parse_attribute_list(
        protocol.ext_x_daterange, line, attribute_parser
    )

    if 'dateranges' not in state:
        state['dateranges'] = []

    state['dateranges'].append(parsed)


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
