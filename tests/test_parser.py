# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import m3u8
import playlists
from m3u8.parser import cast_date_time

def test_should_parse_simple_playlist_from_string():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST)
    assert 5220 == data['targetduration']
    assert 0 == data['media_sequence']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_should_parse_non_integer_duration_from_playlist_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_NON_INTEGER_DURATION)
    assert 5220.5 == data['targetduration']
    assert [5220.5] == [c['duration'] for c in data['segments']]

def test_should_parse_simple_playlist_from_string_with_different_linebreaks():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST.replace('\n', '\r\n'))
    assert 5220 == data['targetduration']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_should_parse_sliding_window_playlist_from_string():
    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert 8 == data['targetduration']
    assert 2680 == data['media_sequence']
    assert ['https://priv.example.com/fileSequence2680.ts',
            'https://priv.example.com/fileSequence2681.ts',
            'https://priv.example.com/fileSequence2682.ts'] == [c['uri'] for c in data['segments']]
    assert [8, 8, 8] == [c['duration'] for c in data['segments']]

def test_should_parse_playlist_with_encripted_segments_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS)
    assert 7794 == data['media_sequence']
    assert 15 == data['targetduration']
    assert 'AES-128' == data['key']['method']
    assert 'https://priv.example.com/key.php?r=52' == data['key']['uri']
    assert ['http://media.example.com/fileSequence52-1.ts',
            'http://media.example.com/fileSequence52-2.ts',
            'http://media.example.com/fileSequence52-3.ts'] == [c['uri'] for c in data['segments']]
    assert [15, 15, 15] == [c['duration'] for c in data['segments']]

def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert "/hls-key/key.bin" == data['key']['uri']
    assert "AES-128" == data['key']['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data['key']['iv']

def test_should_add_key_attribute_to_segment_from_playlist():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS)
    first_segment_key = data['segments'][0]['key']
    assert "/hls-key/key.bin" == first_segment_key['uri']
    assert "AES-128" == first_segment_key['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == first_segment_key['iv']
    last_segment_key = data['segments'][-1]['key']
    assert "/hls-key/key2.bin" == last_segment_key['uri']
    assert "AES-128" == last_segment_key['method']
    assert "0Xcafe8f758ca555115584bb5b3c687f52" == last_segment_key['iv']

def test_should_parse_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_TITLE)
    assert 1 == len(data['segments'])
    assert 5220 == data['segments'][0]['duration']
    assert "A sample title" == data['segments'][0]['title']
    assert "http://media.example.com/entire.ts" == data['segments'][0]['uri']

def test_should_parse_variant_playlist():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST)
    playlists_list = list(data['playlists'])

    assert True == data['is_variant']
    assert None == data['media_sequence']
    assert 4 == len(playlists_list)

    assert 'http://example.com/low.m3u8' == playlists_list[0]['uri']
    assert 1 == playlists_list[0]['stream_info']['program_id']
    assert 1280000 == playlists_list[0]['stream_info']['bandwidth']

    assert 'http://example.com/audio-only.m3u8' == playlists_list[-1]['uri']
    assert 1 == playlists_list[-1]['stream_info']['program_id']
    assert 65000 == playlists_list[-1]['stream_info']['bandwidth']
    assert 'mp4a.40.5,avc1.42801e' == playlists_list[-1]['stream_info']['codecs']

def test_should_parse_variant_playlist_with_average_bandwidth():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_AVERAGE_BANDWIDTH)
    playlists_list = list(data['playlists'])
    assert 1280000 == playlists_list[0]['stream_info']['bandwidth']
    assert 1252345 == playlists_list[0]['stream_info']['average_bandwidth']
    assert 2560000 == playlists_list[1]['stream_info']['bandwidth']
    assert 2466570 == playlists_list[1]['stream_info']['average_bandwidth']
    assert 7680000 == playlists_list[2]['stream_info']['bandwidth']
    assert 7560423 == playlists_list[2]['stream_info']['average_bandwidth']
    assert 65000 == playlists_list[3]['stream_info']['bandwidth']
    assert 63005 == playlists_list[3]['stream_info']['average_bandwidth']

def test_should_parse_variant_playlist_with_iframe_playlists():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_PLAYLISTS)
    iframe_playlists = list(data['iframe_playlists'])

    assert True == data['is_variant']

    assert 4 == len(iframe_playlists)

    assert 1 == iframe_playlists[0]['iframe_stream_info']['program_id']
    assert 151288 == iframe_playlists[0]['iframe_stream_info']['bandwidth']
    assert '624x352' == iframe_playlists[0]['iframe_stream_info']['resolution']
    assert 'avc1.4d001f' == iframe_playlists[0]['iframe_stream_info']['codecs']
    assert 'video-800k-iframes.m3u8' == iframe_playlists[0]['uri']

    assert 38775 == iframe_playlists[-1]['iframe_stream_info']['bandwidth']
    assert 'avc1.4d001f' == (
        iframe_playlists[-1]['iframe_stream_info']['codecs']
    )
    assert 'video-150k-iframes.m3u8' == iframe_playlists[-1]['uri']

def test_should_parse_variant_playlist_with_alt_iframe_playlists_layout():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_ALT_IFRAME_PLAYLISTS_LAYOUT)
    iframe_playlists = list(data['iframe_playlists'])

    assert True == data['is_variant']

    assert 4 == len(iframe_playlists)

    assert 1 == iframe_playlists[0]['iframe_stream_info']['program_id']
    assert 151288 == iframe_playlists[0]['iframe_stream_info']['bandwidth']
    assert '624x352' == iframe_playlists[0]['iframe_stream_info']['resolution']
    assert 'avc1.4d001f' == iframe_playlists[0]['iframe_stream_info']['codecs']
    assert 'video-800k-iframes.m3u8' == iframe_playlists[0]['uri']

    assert 38775 == iframe_playlists[-1]['iframe_stream_info']['bandwidth']
    assert 'avc1.4d001f' == (
        iframe_playlists[-1]['iframe_stream_info']['codecs']
    )
    assert 'video-150k-iframes.m3u8' == iframe_playlists[-1]['uri']

def test_should_parse_iframe_playlist():
    data = m3u8.parse(playlists.IFRAME_PLAYLIST)

    assert True == data['is_i_frames_only']
    assert 4.12 == data['segments'][0]['duration']
    assert '9400@376' == data['segments'][0]['byterange']
    assert 'segment1.ts' == data['segments'][0]['uri']

def test_should_parse_playlist_using_byteranges():
    data = m3u8.parse(playlists.PLAYLIST_USING_BYTERANGES)

    assert False == data['is_i_frames_only']
    assert 10 == data['segments'][0]['duration']
    assert '76242@0' == data['segments'][0]['byterange']
    assert 'segment.ts' == data['segments'][0]['uri']

def test_should_parse_endlist_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST)
    assert True == data['is_endlist']

    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert False == data['is_endlist']

def test_should_parse_ALLOW_CACHE():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert 'no' == data['allow_cache']

def test_should_parse_VERSION():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert '2' == data['version']

def test_should_parse_program_date_time_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)
    assert cast_date_time('2014-08-13T13:36:33+00:00') == data['program_date_time']
