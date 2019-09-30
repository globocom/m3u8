# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import m3u8
import playlists
import pytest
from m3u8.parser import cast_date_time, ParseError

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

def test_should_parse_comma_in_title():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_TITLE_COMMA)
    assert ['Title with a comma, end'] == [c['title'] for c in data['segments']]

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
    assert 'AES-128' == data['keys'][0]['method']
    assert 'https://priv.example.com/key.php?r=52' == data['keys'][0]['uri']
    assert ['http://media.example.com/fileSequence52-1.ts',
            'http://media.example.com/fileSequence52-2.ts',
            'http://media.example.com/fileSequence52-3.ts'] == [c['uri'] for c in data['segments']]
    assert [15, 15, 15] == [c['duration'] for c in data['segments']]

def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert "/hls-key/key.bin" == data['keys'][0]['uri']
    assert "AES-128" == data['keys'][0]['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data['keys'][0]['iv']

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

def test_should_add_non_key_for_multiple_keys_unencrypted_and_encrypted():
    data = m3u8.parse(playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED)
    # First two segments have no Key, so it's not in the dictionary
    assert 'key' not in data['segments'][0]
    assert 'key' not in data['segments'][1]
    third_segment_key = data['segments'][2]['key']
    assert "/hls-key/key.bin" == third_segment_key['uri']
    assert "AES-128" == third_segment_key['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == third_segment_key['iv']
    last_segment_key = data['segments'][-1]['key']
    assert "/hls-key/key2.bin" == last_segment_key['uri']
    assert "AES-128" == last_segment_key['method']
    assert "0Xcafe8f758ca555115584bb5b3c687f52" == last_segment_key['iv']

def test_should_handle_key_method_none_and_no_uri_attr():
    data = m3u8.parse(playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED_NONE_AND_NO_URI_ATTR)
    assert 'key' not in data['segments'][0]
    assert 'key' not in data['segments'][1]
    third_segment_key = data['segments'][2]['key']
    assert "/hls-key/key.bin" == third_segment_key['uri']
    assert "AES-128" == third_segment_key['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == third_segment_key['iv']
    assert "NONE" == data['segments'][6]['key']['method']

def test_should_parse_quoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_QUOTED_TITLE)
    assert 1 == len(data['segments'])
    assert 5220 == data['segments'][0]['duration']
    assert '"A sample title"' == data['segments'][0]['title']
    assert "http://media.example.com/entire.ts" == data['segments'][0]['uri']

def test_should_parse_unquoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_UNQUOTED_TITLE)
    assert 1 == len(data['segments'])
    assert 5220 == data['segments'][0]['duration']
    assert "A sample unquoted title" == data['segments'][0]['title']
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

def test_should_parse_variant_playlist_with_cc_subtitles_and_audio():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_CC_SUBS_AND_AUDIO)
    playlists_list = list(data['playlists'])

    assert True == data['is_variant']
    assert None == data['media_sequence']
    assert 2 == len(playlists_list)

    assert 'http://example.com/with-cc-hi.m3u8' == playlists_list[0]['uri']
    assert 1 == playlists_list[0]['stream_info']['program_id']
    assert 7680000 == playlists_list[0]['stream_info']['bandwidth']
    assert 'cc' == playlists_list[0]['stream_info']['closed_captions']
    assert 'sub' == playlists_list[0]['stream_info']['subtitles']
    assert 'aud' == playlists_list[0]['stream_info']['audio']

    assert 'http://example.com/with-cc-low.m3u8' == playlists_list[-1]['uri']
    assert 1 == playlists_list[-1]['stream_info']['program_id']
    assert 65000 == playlists_list[-1]['stream_info']['bandwidth']
    assert 'cc' == playlists_list[-1]['stream_info']['closed_captions']
    assert 'sub' == playlists_list[-1]['stream_info']['subtitles']
    assert 'aud' == playlists_list[-1]['stream_info']['audio']

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

# This is actually not according to specification but as for example Twitch.tv
# is producing master playlists that have bandwidth as floats (issue 72)
# this tests that this situation does not break the parser and will just
# truncate to a decimal-integer according to specification
def test_should_parse_variant_playlist_with_bandwidth_as_float():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_BANDWIDTH_FLOAT)
    playlists_list = list(data['playlists'])
    assert 1280000 == playlists_list[0]['stream_info']['bandwidth']
    assert 2560000 == playlists_list[1]['stream_info']['bandwidth']
    assert 7680000 == playlists_list[2]['stream_info']['bandwidth']
    assert 65000 == playlists_list[3]['stream_info']['bandwidth']

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
    assert 2 == data['version']

def test_should_parse_program_date_time_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)
    assert cast_date_time('2014-08-13T13:36:33+00:00') == data['program_date_time']

def test_should_parse_scte35_from_playlist():
    data = m3u8.parse(playlists.CUE_OUT_ELEMENTAL_PLAYLIST)
    assert not data['segments'][2]['cue_out']
    assert data['segments'][3]['scte35']
    assert data['segments'][3]['cue_out']
    assert '/DAlAAAAAAAAAP/wFAUAAAABf+//wpiQkv4ARKogAAEBAQAAQ6sodg==' == data['segments'][4]['scte35']
    assert '50' == data['segments'][4]['scte35_duration']

def test_should_parse_envivio_cue_playlist():
    data = m3u8.parse(playlists.CUE_OUT_ENVIVIO_PLAYLIST)
    assert data['segments'][3]['scte35']
    assert data['segments'][3]['cue_out']
    assert '/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A==' == data['segments'][3]['scte35']
    assert '366' == data['segments'][3]['scte35_duration']
    assert data['segments'][4]['cue_out']
    assert '/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A==' == data['segments'][4]['scte35']
    assert '/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A==' == data['segments'][5]['scte35']

def test_parse_simple_playlist_messy():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_MESSY)
    assert 5220 == data['targetduration']
    assert 0 == data['media_sequence']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_parse_simple_playlist_messy_strict():
    with pytest.raises(ParseError) as catch:
        m3u8.parse(playlists.SIMPLE_PLAYLIST_MESSY, strict=True)
    assert str(catch.value) == 'Syntax error in manifest on line 5: JUNK'

def test_commaless_extinf():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_COMMALESS_EXTINF)
    assert 5220 == data['targetduration']
    assert 0 == data['media_sequence']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_commaless_extinf_strict():
    with pytest.raises(ParseError) as e:
        m3u8.parse(playlists.SIMPLE_PLAYLIST_COMMALESS_EXTINF, strict=True)
    assert str(e.value) == 'Syntax error in manifest on line 3: #EXTINF:5220'


def test_should_parse_segment_map_uri():
    data = m3u8.parse(playlists.MAP_URI_PLAYLIST)
    assert data['segment_map']['uri'] == "fileSequence0.mp4"


def test_should_parse_segment_map_uri_with_byterange():
    data = m3u8.parse(playlists.MAP_URI_PLAYLIST_WITH_BYTERANGE)
    assert data['segment_map']['uri'] == "main.mp4"


def test_should_parse_empty_uri_with_base_path():
    data = m3u8.M3U8(
            playlists.MEDIA_WITHOUT_URI_PLAYLIST,
            base_path='base_path', base_uri='base_uri')
    media = data.media[0]
    assert media.uri is None
    assert media.base_path is None
    assert 'base_uri/' == media.base_uri


def test_should_parse_start_with_negative_time_offset():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_START_NEGATIVE_OFFSET)
    assert data['start']['time_offset'] == -2.0
    assert not hasattr(data['start'], 'precise')


def test_should_parse_start_with_precise():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_START_PRECISE)
    assert data['start']['time_offset'] == 10.5
    assert data['start']['precise'] == 'YES'


def test_should_parse_session_data():
    data = m3u8.parse(playlists.SESSION_DATA_PLAYLIST)
    assert data['session_data'][0]['data_id'] == 'com.example.value'
    assert data['session_data'][0]['value'] == 'example'
    assert data['session_data'][0]['language'] == 'en'


def test_should_parse_multiple_session_data():
    data = m3u8.parse(playlists.MULTIPLE_SESSION_DATA_PLAYLIST)

    assert len(data['session_data']) == 4

    assert data['session_data'][0]['data_id'] == 'com.example.value'
    assert data['session_data'][0]['value'] == 'example'
    assert data['session_data'][0]['language'] == 'en'

    assert data['session_data'][1]['data_id'] == 'com.example.value'
    assert data['session_data'][1]['value'] == 'example'
    assert data['session_data'][1]['language'] == 'ru'

    assert data['session_data'][2]['data_id'] == 'com.example.value'
    assert data['session_data'][2]['value'] == 'example'
    assert data['session_data'][2]['language'] == 'de'

    assert data['session_data'][3]['data_id'] == 'com.example.title'
    assert data['session_data'][3]['uri'] == 'title.json'

def test_simple_playlist_with_discontinuity_sequence():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_DISCONTINUITY_SEQUENCE)
    assert data['discontinuity_sequence'] == 123

def test_simple_playlist_with_custom_tags():
    def get_movie(line, data, lineno):
        custom_tag = line.split(':')
        if len(custom_tag) == 2:
            data['movie'] = custom_tag[1].strip()

    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_CUSTOM_TAGS, strict=False, custom_tags_parser=get_movie)
    assert data['movie'] == 'million dollar baby'
    assert 5220 == data['targetduration']
    assert 0 == data['media_sequence']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_master_playlist_with_frame_rate():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_FRAME_RATE)
    playlists_list = list(data['playlists'])
    assert 25 == playlists_list[0]['stream_info']['frame_rate']
    assert 50 == playlists_list[1]['stream_info']['frame_rate']
    assert 60 == playlists_list[2]['stream_info']['frame_rate']
    assert 12.5 == playlists_list[3]['stream_info']['frame_rate']

def test_low_latency_playlist():
    data = m3u8.parse(playlists.LOW_LATENCY_DELTA_UPDATE_PLAYLIST)
    assert data['server_control']['can_block_reload'] == 'YES'
    assert data['server_control']['can_skip_until'] == 12.0
    assert data['server_control']['part_hold_back'] == 1.0
    assert data['part_inf']['part_target'] == 0.33334
    assert data['skip']['skipped_segments'] == 3
    assert len(data['segments'][2]['parts']) == 12
    assert data['segments'][2]['parts'][0]['duration'] == 0.33334
    assert data['segments'][2]['parts'][0]['uri'] == "filePart271.0.ts"
    assert len(data['rendition_reports']) == 2
    assert data['rendition_reports'][0]['uri'] == "../1M/waitForMSN.php"
    assert data['rendition_reports'][0]['last_msn'] == 273
    assert data['rendition_reports'][0]['last_part'] == 3
