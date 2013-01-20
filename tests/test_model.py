'''
Tests M3U8 class to make sure all attributes and methods use the correct
data returned from parser.parse()

'''

import m3u8
from playlists import *

def test_target_duration_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'targetduration': '1234567'})

    assert '1234567' == obj.target_duration

def test_media_sequence_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'media_sequence': '1234567'})

    assert '1234567' == obj.media_sequence

def test_key_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    data = {'key': {'method': 'AES-128',
                    'uri': '/key',
                    'iv': 'foobar'}}
    mock_parser_data(obj, data)

    assert 'Key' == obj.key.__class__.__name__
    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert 'foobar' == obj.key.iv

def test_key_attribute_on_none():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {})

    assert None == obj.key

def test_key_attribute_without_initialization_vector():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'key': {'method': 'AES-128',
                                   'uri': '/key'}})

    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert None == obj.key.iv

def test_segments_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
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
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'duration': 1500}]})

    assert 1 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 1500 == obj.segments[0].duration
    assert None == obj.segments[0].title

def test_segments_attribute_without_duration():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'segments': [{'uri': '/foo/bar-1.ts',
                                         'title': 'Segment title'}]})

    assert 1 == len(obj.segments)

    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'Segment title' == obj.segments[0].title
    assert None == obj.segments[0].duration

def test_is_variant_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'is_variant': False})
    assert not obj.is_variant

    mock_parser_data(obj, {'is_variant': True})
    assert obj.is_variant

def test_is_endlist_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'is_endlist': False})
    assert not obj.is_endlist

    obj = m3u8.M3U8(SLIDING_WINDOW_PLAYLIST)
    mock_parser_data(obj, {'is_endlist': True})
    assert obj.is_endlist

def test_playlists_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    data = {'playlists': [{'uri': '/url/1.m3u8',
                           'stream_info': {'program_id': '1',
                                           'bandwidth': '320000'}},
                          {'uri': '/url/2.m3u8',
                           'stream_info': {'program_id': '1',
                                           'bandwidth': '120000',
                                           'codecs': 'mp4a.40.5'}},
                          ]}
    mock_parser_data(obj, data)

    assert 2 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].uri
    assert '1' == obj.playlists[0].stream_info.program_id
    assert '320000' == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs

    assert '/url/2.m3u8' == obj.playlists[1].uri
    assert '1' == obj.playlists[1].stream_info.program_id
    assert '120000' == obj.playlists[1].stream_info.bandwidth
    assert 'mp4a.40.5' == obj.playlists[1].stream_info.codecs

def test_playlists_attribute_without_program_id():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'playlists': [{'uri': '/url/1.m3u8',
                                          'stream_info': {'bandwidth': '320000'}}
                                         ]})

    assert 1 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].uri
    assert '320000' == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs
    assert None == obj.playlists[0].stream_info.program_id

def test_playlists_attribute_with_resolution():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST_WITH_RESOLUTION)

    assert 2 == len(obj.playlists)
    assert (512, 288) == obj.playlists[0].stream_info.resolution
    assert None == obj.playlists[1].stream_info.resolution

def test_version_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'version': '2'})
    assert '2' == obj.version

    mock_parser_data(obj, {})
    assert None == obj.version

def test_allow_cache_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    mock_parser_data(obj, {'allow_cache': 'no'})
    assert 'no' == obj.allow_cache

    mock_parser_data(obj, {})
    assert None == obj.allow_cache

def test_files_attribute_should_list_all_files_including_segments_and_key():
    obj = m3u8.M3U8(PLAYLIST_WITH_ENCRIPTED_SEGMENTS)
    files = [
        'https://priv.example.com/key.php?r=52',
        'http://media.example.com/fileSequence52-1.ts',
        'http://media.example.com/fileSequence52-2.ts',
        'http://media.example.com/fileSequence52-3.ts',
        ]
    assert files == obj.files


# dump m3u8

def test_dumps_should_build_same_string():
    playlists = [PLAYLIST_WITH_NON_INTEGER_DURATION, PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV]
    for playlist in playlists:
        obj = m3u8.M3U8(playlist)
        expected = playlist.replace(', IV', ',IV').strip()
        assert expected == obj.dumps().strip()

def test_dump_playlists_with_resolution():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST_WITH_RESOLUTION)

    expected = SIMPLE_PLAYLIST_WITH_RESOLUTION.strip().splitlines()

    assert expected == obj.dumps().strip().splitlines()

def test_dump_should_build_file_with_same_content(tmpdir):
    obj = m3u8.M3U8(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)

    expected = PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV.replace(', IV', ',IV').strip()
    filename = str(tmpdir.join('playlist.m3u8'))

    obj.dump(filename)

    assert_file_content(filename, expected)

def test_dump_should_create_sub_directories(tmpdir):
    obj = m3u8.M3U8(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)

    expected = PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV.replace(', IV', ',IV').strip()
    filename = str(tmpdir.join('subdir1', 'subdir2', 'playlist.m3u8'))

    obj.dump(filename)

    assert_file_content(filename, expected)

def test_dump_should_work_for_variant_streams():
    obj = m3u8.M3U8(VARIANT_PLAYLIST)

    expected = VARIANT_PLAYLIST.replace(', BANDWIDTH', ',BANDWIDTH').strip()

    assert expected == obj.dumps().strip()

def test_should_dump_with_endlist_tag():
    obj = m3u8.M3U8(SLIDING_WINDOW_PLAYLIST)
    obj.is_endlist= True

    assert '#EXT-X-ENDLIST' in obj.dumps().splitlines()

def test_should_dump_without_endlist_tag():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.is_endlist = False

    expected  = SIMPLE_PLAYLIST.strip().splitlines()
    expected.remove('#EXT-X-ENDLIST')

    assert expected == obj.dumps().strip().splitlines()

def test_should_normalize_segments_and_key_urls_if_basepath_passed_to_constructor():
    basepath = 'http://videoserver.com/hls/live'

    obj = m3u8.M3U8(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV, basepath)

    expected = PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV \
        .replace(', IV', ',IV') \
        .replace('../../../../hls', basepath) \
        .replace('/hls-key', basepath) \
        .strip()

    assert obj.dumps().strip() == expected

def test_should_normalize_variant_streams_urls_if_basepath_passed_to_constructor():
    basepath = 'http://videoserver.com/hls/live'
    obj = m3u8.M3U8(VARIANT_PLAYLIST, basepath)

    expected = VARIANT_PLAYLIST \
        .replace(', BANDWIDTH', ',BANDWIDTH') \
        .replace('http://example.com', basepath) \
        .strip()

    assert obj.dumps().strip() == expected


def test_should_normalize_segments_and_key_urls_if_basepath_attribute_updated():
    basepath = 'http://videoserver.com/hls/live'

    obj = m3u8.M3U8(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    obj.basepath = basepath

    expected = PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV \
        .replace(', IV', ',IV') \
        .replace('../../../../hls', basepath) \
        .replace('/hls-key', basepath) \
        .strip()

    assert obj.dumps().strip() == expected

def test_m3u8_should_propagate_baseuri_to_segments():
    with open(RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.M3U8(content, baseuri='/any/path')
    assert '/entire1.ts' == obj.segments[0].uri
    assert '/any/path/entire1.ts' == obj.segments[0].absolute_uri
    obj.baseuri = '/any/where/'
    assert '/entire1.ts' == obj.segments[0].uri
    assert '/any/where/entire1.ts' == obj.segments[0].absolute_uri

def test_m3u8_should_propagate_baseuri_to_key():
    with open(RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.M3U8(content, baseuri='/any/path')
    assert '../key.bin' == obj.key.uri
    assert '/any/key.bin' == obj.key.absolute_uri
    obj.baseuri = '/any/where/'
    assert '../key.bin' == obj.key.uri
    assert '/any/key.bin' == obj.key.absolute_uri

def test_dump_should_work_with_iframe_playlist():
    content = SIMPLE_IFRAME_PLAYLIST
    obj = m3u8.M3U8(content, baseuri = 'any/path')
    assert 'main.ts' == obj.segments[0].uri
    assert 'any/path/main.ts' == obj.segments[0].absolute_uri
    obj.baseuri = 'http://videoserver.com/hls/live'
    assert 'http://videoserver.com/hls/live/main.ts' == obj.segments[0].absolute_uri
    assert obj.dumps().strip() == content.strip()

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
