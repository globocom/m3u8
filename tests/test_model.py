# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

#Tests M3U8 class to make sure all attributes and methods use the correct
#data returned from parser.parse()

import arrow
import datetime
import m3u8
import playlists
from m3u8.model import Segment

def test_target_duration_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'targetduration': '1234567'})

    assert '1234567' == obj.target_duration

def test_media_sequence_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'media_sequence': '1234567'})

    assert '1234567' == obj.media_sequence

def test_program_date_time_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)

    assert arrow.get('2014-08-13T13:36:33+00:00').datetime == obj.program_date_time

def test_program_date_time_attribute_for_each_segment():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)

    first_program_date_time = arrow.get('2014-08-13T13:36:33+00:00').datetime
    for idx, segment in enumerate(obj.segments):
        assert segment.program_date_time == first_program_date_time + datetime.timedelta(seconds=idx * 3)

def test_program_date_time_attribute_with_discontinuity():
    obj = m3u8.M3U8(playlists.DISCONTINUITY_PLAYLIST_WITH_PROGRAM_DATE_TIME)

    first_program_date_time = arrow.get('2014-08-13T13:36:33+00:00').datetime
    discontinuity_program_date_time = arrow.get('2014-08-13T13:36:55+00:00').datetime

    segments = obj.segments

    assert segments[0].program_date_time == first_program_date_time
    assert segments[5].program_date_time == discontinuity_program_date_time
    assert segments[6].program_date_time == discontinuity_program_date_time + datetime.timedelta(seconds=3)


def test_segment_discontinuity_attribute():
    obj = m3u8.M3U8(playlists.DISCONTINUITY_PLAYLIST_WITH_PROGRAM_DATE_TIME)
    segments = obj.segments

    assert segments[0].discontinuity == False
    assert segments[5].discontinuity == True
    assert segments[6].discontinuity == False

def test_segment_cue_out_attribute():
    obj = m3u8.M3U8(playlists.CUE_OUT_PLAYLIST)
    segments = obj.segments

    assert segments[0].cue_out == True
    assert segments[1].cue_out == True
    assert segments[2].cue_out == True

def test_key_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    data = {'key': {'method': 'AES-128',
                    'uri': '/key',
                    'iv': 'foobar'}}
    mock_parser_data(obj, data)

    assert 'Key' == obj.key.__class__.__name__
    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert 'foobar' == obj.key.iv

def test_key_attribute_on_none():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {})

    assert None == obj.key

def test_key_attribute_without_initialization_vector():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'key': {'method': 'AES-128',
                                   'uri': '/key'}})

    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert None == obj.key.iv

def test_segments_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'title': 'First Segment',
                                         'duration': 1500},
                                        {'uri': '/foo/bar-2.ts',
                                         'title': 'Second Segment',
                                         'duration': 1600}]})

    assert 2 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'First Segment' == obj.segments[0].title
    assert 1500 == obj.segments[0].duration

def test_segments_attribute_without_title():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'duration': 1500}]})

    assert 1 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 1500 == obj.segments[0].duration
    assert None == obj.segments[0].title

def test_segments_attribute_without_duration():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'title': 'Segment title'}]})

    assert 1 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'Segment title' == obj.segments[0].title
    assert None == obj.segments[0].duration

def test_segments_attribute_with_byterange():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'title': 'Segment title',
                                         'duration': 1500,
                                         'byterange': '76242@0'}]})

    assert 1 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'Segment title' == obj.segments[0].title
    assert 1500 == obj.segments[0].duration
    assert '76242@0' == obj.segments[0].byterange

def test_segment_attribute_with_multiple_keys():
    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS)

    segments = obj.segments
    assert segments[0].key.uri == '/hls-key/key.bin'
    assert segments[1].key.uri == '/hls-key/key.bin'
    assert segments[4].key.uri == '/hls-key/key2.bin'
    assert segments[5].key.uri == '/hls-key/key2.bin'


def test_is_variant_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'is_variant': False})
    assert not obj.is_variant

    mock_parser_data(obj, {'is_variant': True})
    assert obj.is_variant

def test_is_endlist_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'is_endlist': False})
    assert not obj.is_endlist

    obj = m3u8.M3U8(playlists.SLIDING_WINDOW_PLAYLIST)
    mock_parser_data(obj, {'is_endlist': True})
    assert obj.is_endlist

def test_is_i_frames_only_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'is_i_frames_only': False})
    assert not obj.is_i_frames_only

    mock_parser_data(obj, {'is_i_frames_only': True})
    assert obj.is_i_frames_only

def test_playlists_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    data = {'playlists': [{'uri': '/url/1.m3u8',
                           'stream_info': {'program_id': 1,
                                           'bandwidth': 320000,
                                           'video': 'high'}},
                          {'uri': '/url/2.m3u8',
                           'stream_info': {'program_id': 1,
                                           'bandwidth': 120000,
                                           'codecs': 'mp4a.40.5',
                                           'video': 'low'}},
                          ],
            'media': [{'type': 'VIDEO', 'name': 'High', 'group_id': 'high'},
                      {'type': 'VIDEO', 'name': 'Low', 'group_id': 'low',
                       'default': 'YES', 'autoselect': 'YES'}
                     ]
           }
    mock_parser_data(obj, data)

    assert 2 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].uri
    assert 1 == obj.playlists[0].stream_info.program_id
    assert 320000 == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs

    assert None == obj.playlists[0].media[0].uri
    assert 'high' == obj.playlists[0].media[0].group_id
    assert 'VIDEO' == obj.playlists[0].media[0].type
    assert None == obj.playlists[0].media[0].language
    assert 'High' == obj.playlists[0].media[0].name
    assert None == obj.playlists[0].media[0].default
    assert None == obj.playlists[0].media[0].autoselect
    assert None == obj.playlists[0].media[0].forced
    assert None == obj.playlists[0].media[0].characteristics

    assert '/url/2.m3u8' == obj.playlists[1].uri
    assert 1 == obj.playlists[1].stream_info.program_id
    assert 120000 == obj.playlists[1].stream_info.bandwidth
    assert 'mp4a.40.5' == obj.playlists[1].stream_info.codecs

    assert None == obj.playlists[1].media[0].uri
    assert 'low' == obj.playlists[1].media[0].group_id
    assert 'VIDEO' == obj.playlists[1].media[0].type
    assert None == obj.playlists[1].media[0].language
    assert 'Low' == obj.playlists[1].media[0].name
    assert 'YES' == obj.playlists[1].media[0].default
    assert 'YES' == obj.playlists[1].media[0].autoselect
    assert None == obj.playlists[1].media[0].forced
    assert None == obj.playlists[1].media[0].characteristics

    assert [] == obj.iframe_playlists

def test_playlists_attribute_without_program_id():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'playlists': [{'uri': '/url/1.m3u8',
                                          'stream_info': {'bandwidth': 320000}}
                                         ]})

    assert 1 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].uri
    assert 320000 == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs
    assert None == obj.playlists[0].stream_info.program_id

def test_playlists_attribute_with_resolution():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_RESOLUTION)

    assert 2 == len(obj.playlists)
    assert (512, 288) == obj.playlists[0].stream_info.resolution
    assert None == obj.playlists[1].stream_info.resolution

def test_iframe_playlists_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    data = {
        'iframe_playlists': [{'uri': '/url/1.m3u8',
                              'iframe_stream_info': {'program_id': 1,
                                                     'bandwidth': 320000,
                                                     'resolution': '320x180',
                                                     'codecs': 'avc1.4d001f'}},
                             {'uri': '/url/2.m3u8',
                              'iframe_stream_info': {'bandwidth': '120000',
                                                     'codecs': 'avc1.4d400d'}}]
    }
    mock_parser_data(obj, data)

    assert 2 == len(obj.iframe_playlists)

    assert '/url/1.m3u8' == obj.iframe_playlists[0].uri
    assert 1 == obj.iframe_playlists[0].iframe_stream_info.program_id
    assert 320000 == obj.iframe_playlists[0].iframe_stream_info.bandwidth
    assert (320, 180) == obj.iframe_playlists[0].iframe_stream_info.resolution
    assert 'avc1.4d001f' == obj.iframe_playlists[0].iframe_stream_info.codecs

    assert '/url/2.m3u8' == obj.iframe_playlists[1].uri
    assert None == obj.iframe_playlists[1].iframe_stream_info.program_id
    assert '120000' == obj.iframe_playlists[1].iframe_stream_info.bandwidth
    assert None == obj.iframe_playlists[1].iframe_stream_info.resolution
    assert 'avc1.4d400d' == obj.iframe_playlists[1].iframe_stream_info.codecs

def test_version_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'version': '2'})
    assert '2' == obj.version

    mock_parser_data(obj, {})
    assert None == obj.version

def test_allow_cache_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'allow_cache': 'no'})
    assert 'no' == obj.allow_cache

    mock_parser_data(obj, {})
    assert None == obj.allow_cache

def test_files_attribute_should_list_all_files_including_segments_and_key():
    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS)
    files = [
        'https://priv.example.com/key.php?r=52',
        'http://media.example.com/fileSequence52-1.ts',
        'http://media.example.com/fileSequence52-2.ts',
        'http://media.example.com/fileSequence52-3.ts',
        ]
    assert files == obj.files

def test_vod_playlist_type_should_be_imported_as_a_simple_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_VOD_PLAYLIST_TYPE)
    assert obj.playlist_type == 'vod'

def test_event_playlist_type_should_be_imported_as_a_simple_attribute():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_EVENT_PLAYLIST_TYPE)
    assert obj.playlist_type == 'event'

def test_independent_segments_should_be_true():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_INDEPENDENT_SEGMENTS)
    assert obj.is_independent_segments

def test_independent_segments_should_be_false():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_EVENT_PLAYLIST_TYPE)
    assert not obj.is_independent_segments

def test_no_playlist_type_leaves_attribute_empty():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    assert obj.playlist_type is None


# dump m3u8

def test_dumps_should_build_same_string():
    playlists_model = [playlists.PLAYLIST_WITH_NON_INTEGER_DURATION, playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV]
    for playlist in playlists_model:
        obj = m3u8.M3U8(playlist)
        expected = playlist.replace(', IV', ',IV').strip()
        assert expected == obj.dumps().strip()

def test_dump_playlists_with_resolution():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_RESOLUTION)

    expected = playlists.SIMPLE_PLAYLIST_WITH_RESOLUTION.strip().splitlines()

    assert expected == obj.dumps().strip().splitlines()

def test_dump_should_build_file_with_same_content(tmpdir):
    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)

    expected = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV.replace(', IV', ',IV').strip()
    filename = str(tmpdir.join('playlist.m3u8'))

    obj.dump(filename)

    assert_file_content(filename, expected)

def test_dump_should_create_sub_directories(tmpdir):
    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)

    expected = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV.replace(', IV', ',IV').strip()
    filename = str(tmpdir.join('subdir1', 'subdir2', 'playlist.m3u8'))

    obj.dump(filename)

    assert_file_content(filename, expected)

def test_dump_should_work_for_variant_streams():
    obj = m3u8.M3U8(playlists.VARIANT_PLAYLIST)

    expected = playlists.VARIANT_PLAYLIST.replace(', BANDWIDTH', ',BANDWIDTH').strip()

    assert expected == obj.dumps().strip()

def test_dump_should_work_for_variant_playlists_with_iframe_playlists():
    obj = m3u8.M3U8(playlists.VARIANT_PLAYLIST_WITH_IFRAME_PLAYLISTS)

    expected = playlists.VARIANT_PLAYLIST_WITH_IFRAME_PLAYLISTS.strip()

    assert expected == obj.dumps().strip()

def test_dump_should_work_for_iframe_playlists():
    obj = m3u8.M3U8(playlists.IFRAME_PLAYLIST)

    expected = playlists.IFRAME_PLAYLIST.strip()

    assert expected == obj.dumps().strip()

    obj = m3u8.M3U8(playlists.IFRAME_PLAYLIST2)

    expected = playlists.IFRAME_PLAYLIST.strip()

    # expected that dump will reverse EXTINF and EXT-X-BYTERANGE,
    # hence IFRAME_PLAYLIST dump from IFRAME_PLAYLIST2 parse.
    assert expected == obj.dumps().strip()

    obj = m3u8.M3U8(playlists.IFRAME_PLAYLIST2)

    expected = playlists.IFRAME_PLAYLIST.strip()

    # expected that dump will reverse EXTINF and EXT-X-BYTERANGE,
    # hence IFRAME_PLAYLIST dump from IFRAME_PLAYLIST2 parse.
    assert expected == obj.dumps().strip()

def test_dump_should_include_program_date_time():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)

    assert "EXT-X-PROGRAM-DATE-TIME:2014-08-13T13:36:33+00:00" in obj.dumps().strip()

def test_dump_should_work_for_playlists_using_byteranges():
    obj = m3u8.M3U8(playlists.PLAYLIST_USING_BYTERANGES)

    expected = playlists.PLAYLIST_USING_BYTERANGES.strip()

    assert expected == obj.dumps().strip()

def test_should_dump_with_endlist_tag():
    obj = m3u8.M3U8(playlists.SLIDING_WINDOW_PLAYLIST)
    obj.is_endlist= True

    assert '#EXT-X-ENDLIST' in obj.dumps().splitlines()

def test_should_dump_without_endlist_tag():
    obj = m3u8.M3U8(playlists.SIMPLE_PLAYLIST)
    obj.is_endlist = False

    expected  = playlists.SIMPLE_PLAYLIST.strip().splitlines()
    expected.remove('#EXT-X-ENDLIST')

    assert expected == obj.dumps().strip().splitlines()

def test_should_dump_multiple_keys():
    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS)
    expected  = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS.strip()

    assert expected == obj.dumps().strip()

def test_should_dump_program_datetime_and_discontinuity():
    obj = m3u8.M3U8(playlists.DISCONTINUITY_PLAYLIST_WITH_PROGRAM_DATE_TIME)
    expected  = playlists.DISCONTINUITY_PLAYLIST_WITH_PROGRAM_DATE_TIME.strip()

    assert expected == obj.dumps().strip()

def test_should_normalize_segments_and_key_urls_if_base_path_passed_to_constructor():
    base_path = 'http://videoserver.com/hls/live'

    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV, base_path)

    expected = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV \
        .replace(', IV', ',IV') \
        .replace('../../../../hls', base_path) \
        .replace('/hls-key', base_path) \
        .strip()

    assert obj.dumps().strip() == expected

def test_should_normalize_variant_streams_urls_if_base_path_passed_to_constructor():
    base_path = 'http://videoserver.com/hls/live'
    obj = m3u8.M3U8(playlists.VARIANT_PLAYLIST, base_path)

    expected = playlists.VARIANT_PLAYLIST \
        .replace(', BANDWIDTH', ',BANDWIDTH') \
        .replace('http://example.com', base_path) \
        .strip()

    assert obj.dumps().strip() == expected

def test_should_normalize_segments_and_key_urls_if_base_path_attribute_updated():
    base_path = 'http://videoserver.com/hls/live'

    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    obj.base_path = base_path     # update later

    expected = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV \
        .replace(', IV', ',IV') \
        .replace('../../../../hls', base_path) \
        .replace('/hls-key', base_path) \
        .strip()

    assert obj.dumps() == expected

def test_should_normalize_segments_and_key_urls_if_base_path_attribute_updated():
    base_path = 'http://videoserver.com/hls/live'

    obj = m3u8.M3U8(playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    obj.base_path = base_path

    expected = playlists.PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV \
        .replace(', IV', ',IV') \
        .replace('../../../../hls', base_path) \
        .replace('/hls-key', base_path) \
        .strip()

    assert obj.dumps().strip() == expected

def test_playlist_type_dumped_to_appropriate_m3u8_field():
    obj = m3u8.M3U8()
    obj.playlist_type = 'vod'
    result = obj.dumps()
    expected = '#EXTM3U\n#EXT-X-PLAYLIST-TYPE:VOD\n'
    assert result == expected

def test_empty_playlist_type_is_gracefully_ignored():
    obj = m3u8.M3U8()
    obj.playlist_type = ''
    result = obj.dumps()
    expected = '#EXTM3U\n'
    assert result == expected

def test_none_playlist_type_is_gracefully_ignored():
    obj = m3u8.M3U8()
    obj.playlist_type = None
    result = obj.dumps()
    expected = '#EXTM3U\n'
    assert result == expected

def test_0_media_sequence_added_to_file():
    obj = m3u8.M3U8()
    obj.media_sequence = 0
    result = obj.dumps()
    expected = '#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:0\n'
    assert result == expected

def test_none_media_sequence_gracefully_ignored():
    obj = m3u8.M3U8()
    obj.media_sequence = None
    result = obj.dumps()
    expected = '#EXTM3U\n'
    assert result == expected

def test_should_correctly_update_base_path_if_its_blank():
    segment = Segment('entire.ts', 'http://1.2/')
    assert not segment.base_path
    segment.base_path = "base_path"
    assert "http://1.2/base_path/entire.ts" == segment.absolute_uri

def test_m3u8_should_propagate_base_uri_to_segments():
    with open(playlists.RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.M3U8(content, base_uri='/any/path')
    assert '/entire1.ts' == obj.segments[0].uri
    assert '/any/path/entire1.ts' == obj.segments[0].absolute_uri
    assert 'entire4.ts' == obj.segments[3].uri
    assert '/any/path/entire4.ts' == obj.segments[3].absolute_uri
    obj.base_uri = '/any/where/'
    assert '/entire1.ts' == obj.segments[0].uri
    assert '/any/where/entire1.ts' == obj.segments[0].absolute_uri
    assert 'entire4.ts' == obj.segments[3].uri
    assert '/any/where/entire4.ts' == obj.segments[3].absolute_uri

def test_m3u8_should_propagate_base_uri_to_key():
    with open(playlists.RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.M3U8(content, base_uri='/any/path')
    assert '../key.bin' == obj.key.uri
    assert '/any/key.bin' == obj.key.absolute_uri
    obj.base_uri = '/any/where/'
    assert '../key.bin' == obj.key.uri
    assert '/any/key.bin' == obj.key.absolute_uri


# custom asserts

def assert_file_content(filename, expected):
    with open(filename) as fileobj:
        content = fileobj.read().strip()

    assert content == expected


# helpers

def mock_parser_data(m3u8_obj, data):
    data.setdefault('segments', [])
    m3u8_obj.data = data
    m3u8_obj._initialize_attributes()
