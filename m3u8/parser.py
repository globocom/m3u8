# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import iso8601
import datetime
import itertools
import re
<<<<<<< HEAD

'''
Standard Tags
'''
extm3u = '#EXTM3U'
extinf = '#EXTINF'

'''
New Tags
'''
ext_x_byterange = '#EXT-X-BYTERANGE'
ext_x_targetduration = '#EXT-X-TARGETDURATION'
ext_x_media_sequence = '#EXT-X-MEDIA-SEQUENCE'
ext_x_key = '#EXT-X-KEY'
ext_x_program_date_time = '#EXT-X-PROGRAM-DATE-TIME'
ext_x_allow_cache = '#EXT-X-ALLOW-CACHE'
ext_x_playlist_type = '#EXT-X-PLAYLIST-TYPE'
ext_x_endlist = '#EXT-X-ENDLIST'
ext_x_media = '#EXT-X-MEDIA'
ext_x_stream_inf = '#EXT-X-STREAM-INF'
ext_x_discontinuity = '#EXT-X-DISCONTINUITY'
ext_x_i_frames_only = '#EXT-X-I-FRAMES-ONLY'
ext_x_map = '#EXT-X-MAP'
ext_x_i_frame_stream_inf = '#EXT-X-I-FRAME-STREAM-INF'
ext_x_version = '#EXT-X-VERSION'
ext_x_allow_cache = '#EXT-X-ALLOW-CACHE'
ext_x_endlist = '#EXT-X-ENDLIST'
extinf = '#EXTINF'
=======
from m3u8 import protocol
import exceptions
>>>>>>> globocom/master

'''
http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.2
http://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
'''
ATTRIBUTELISTPATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')

<<<<<<< HEAD

def parse(content):
=======
def cast_date_time(value):
    return iso8601.parse_date(value)

def format_date_time(value):
    return value.isoformat()

class ParseError(exceptions.Exception):
    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line

    def __str__(self):
        return 'Syntax error in manifest on line %d: %s' % (self.lineno, self.line)

def parse(content, strict=False):
>>>>>>> globocom/master
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    data = {
        'media_sequence': 0,
        'is_variant': False,
        'is_endlist': False,
        'is_i_frames_only': False,
<<<<<<< HEAD
=======
        'is_independent_segments': False,
        'playlist_type': None,
>>>>>>> globocom/master
        'playlists': [],
        'iframe_playlists': [],
        'segments': [],
<<<<<<< HEAD
        'map': None,
        'iframe_playlists': []
=======
        'media': [],
>>>>>>> globocom/master
        }

    state = {
        'expect_segment': False,
        'expect_playlist': False,
        'expect_i_frame_playlist': False
        }

    lineno = 0
    for line in string_to_lines(content):
        lineno += 1
        line = line.strip()

<<<<<<< HEAD
        if line.startswith(ext_x_byterange):
            _parse_simple_parameter(line, data)
            state['expect_segment'] = True

        elif line.startswith(extinf):
            _parse_extinf(line, data, state)
            state['expect_segment'] = True

        elif line.startswith(ext_x_key):
            _parse_key(line, data, state)

        elif state['expect_segment']:
            _parse_ts_chunk(line, data, state)
            state['expect_segment'] = False

        elif state['expect_playlist']:
            _parse_variant_playlist(line, data, state)
            state['expect_playlist'] = False

        elif state['expect_i_frame_playlist']:
            _parse_i_frame_playlist(line, data, state)
            state['expect_i_frame_playlist'] = False

        elif line == ext_x_i_frames_only:
            data['is_i_frames_only'] = True
        elif line.startswith(ext_x_targetduration):
=======
        if line.startswith(protocol.ext_x_byterange):
            _parse_byterange(line, state)
            state['expect_segment'] = True

        elif line.startswith(protocol.ext_x_targetduration):
>>>>>>> globocom/master
            _parse_simple_parameter(line, data, float)

        elif line.startswith(protocol.ext_x_media_sequence):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_program_date_time):
            _, program_date_time = _parse_simple_parameter_raw_value(line, cast_date_time)
            if not data.get('program_date_time'):
                data['program_date_time'] = program_date_time
            state['current_program_date_time'] = program_date_time

        elif line.startswith(protocol.ext_x_discontinuity):
            state['discontinuity'] = True

        elif line.startswith(protocol.ext_x_cue_out):
            state['cue_out'] = True

        elif line.startswith(protocol.ext_x_version):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_x_allow_cache):
            _parse_simple_parameter(line, data)
<<<<<<< HEAD
        elif line.startswith(ext_x_playlist_type):
            _parse_simple_parameter(line, data)

        elif line.startswith(ext_x_stream_inf):
=======

        elif line.startswith(protocol.ext_x_key):
            state['current_key'] = _parse_key(line)
            data['key'] = data.get('key', state['current_key'])

        elif line.startswith(protocol.extinf):
            _parse_extinf(line, data, state)
            state['expect_segment'] = True

        elif line.startswith(protocol.ext_x_stream_inf):
            state['expect_playlist'] = True
>>>>>>> globocom/master
            _parse_stream_inf(line, data, state)
            state['expect_playlist'] = True

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

<<<<<<< HEAD
        elif line.startswith(ext_x_i_frame_stream_inf):
            _parse_i_frame_stream_info(line, data, state)
            state['expect_i_frame_playlist'] = True

        elif line.startswith(ext_x_map):
            _parse_map(line, data)

    return data


def _parse_key(line, data, state):
    params = ATTRIBUTELISTPATTERN.split(line.replace(ext_x_key + ':', ''))[1::2]
    data['key'] = {}
=======
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
>>>>>>> globocom/master
    for param in params:
        name, value = param.split('=', 1)
        key[normalize_attribute(name)] = remove_quotes(value)
    return key


def _parse_extinf(line, data, state):
    duration, title = line.replace(protocol.extinf + ':', '').split(',')
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
<<<<<<< HEAD
    if 'key' in data:
        segment['key'] = data['key']
    if 'byterange' in data:
        segment['byterange'] = data['byterange']
        del data['byterange']
    data['segments'].append(segment)


def _parse_stream_inf(line, data, state):
    params = ATTRIBUTELISTPATTERN.split(line.replace(ext_x_stream_inf + ':', ''))[1::2]
=======
    segment['cue_out'] = state.pop('cue_out', False)
    segment['discontinuity'] = state.pop('discontinuity', False)
    if state.get('current_key'):
      segment['key'] = state['current_key']
    data['segments'].append(segment)

def _parse_attribute_list(prefix, line, atribute_parser):
    params = ATTRIBUTELISTPATTERN.split(line.replace(prefix + ':', ''))[1::2]
>>>>>>> globocom/master

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
    atribute_parser = remove_quotes_parser('codecs', 'audio', 'video', 'subtitles')
    atribute_parser["program_id"] = int
    atribute_parser["bandwidth"] = int
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


def _parse_i_frame_stream_info(line, data, state):
    '''
    http://tools.ietf.org/html/draft-pantos-http-live-streaming-10#section-3.4.14
    '''
    params = ATTRIBUTELISTPATTERN.split(line.replace(ext_x_i_frame_stream_inf + ':', ''))[1::2]

    i_frame_stream_info = {}
    for param in params:
        name, value = param.split('=', 1)
        i_frame_stream_info[normalize_attribute(name)] = value

    if 'uri' not in i_frame_stream_info and 'bandwidth' not in i_frame_stream_info:
        pass

    state['i_frame_stream_info'] = i_frame_stream_info


def _parse_map(line, data):
    params = ATTRIBUTELISTPATTERN.split(line.replace(ext_x_map + ':', ''))[1::2]
    x_map = {}
    for param in params:
        name, value = param.split('=', 1)
        x_map[normalize_attribute(name)] = value
    data['map'] = x_map


def _parse_variant_playlist(line, data, state):
    playlist = {'uri': line,
                'stream_info': state.pop('stream_info')}

    data['playlists'].append(playlist)

<<<<<<< HEAD

def _parse_i_frame_playlist(line, data, state):
    inf = state.pop('i_frame_stream_info')
    playlist = {'uri': inf['uri'],
                'stream_info': inf}

    data['iframe_playlists'].append(playlist)


def _parse_simple_parameter(line, data, cast_to=str):
=======
def _parse_byterange(line, state):
    if 'segment' not in state:
        state['segment'] = {}
    state['segment']['byterange'] = line.replace(protocol.ext_x_byterange + ':', '')

def _parse_simple_parameter_raw_value(line, cast_to=str, normalize=False):
>>>>>>> globocom/master
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


def string_to_lines(string):
    return string.strip().replace('\r\n', '\n').split('\n')

<<<<<<< HEAD
=======
def remove_quotes_parser(*attrs):
    return dict(zip(attrs, itertools.repeat(remove_quotes)))
>>>>>>> globocom/master

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


def normalize_attribute(attribute):
    return attribute.replace('-', '_').lower().strip()


def is_url(uri):
    return re.match(r'https?://', uri) is not None
