'''
Tests M3U8 class to make sure all attributes and methods use the correct
data returned from parser.parse()

'''

import m3u8
from playlists import SIMPLE_PLAYLIST

def test_target_duration_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'targetduration': '1234567'}

    assert '1234567' == obj.target_duration

def test_media_sequence_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'media_sequence': '1234567'}

    assert '1234567' == obj.media_sequence

def test_key_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'key': {'method': 'AES-128',
                        'uri': '/key',
                        'iv': 'foobar'}}

    assert 'Key' == obj.key.__class__.__name__
    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert 'foobar' == obj.key.iv

def test_key_attribute_on_none():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {}

    assert None == obj.key

def test_key_attribute_without_initialization_vector():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'key': {'method': 'AES-128',
                        'uri': '/key'}}

    assert 'AES-128' == obj.key.method
    assert '/key' == obj.key.uri
    assert None == obj.key.iv

def test_segments_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'segments': [{'uri': '/foo/bar-1.ts',
                              'title': 'First Segment',
                              'duration': 1500},
                             {'uri': '/foo/bar-2.ts',
                              'title': 'Second Segment',
                              'duration': 1600}]}

    assert 2 == len(obj.segments)

    assert 'Segment' == obj.segments[0].__class__.__name__
    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'First Segment' == obj.segments[0].title
    assert 1500 == obj.segments[0].duration

def test_segments_attribute_without_title():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'segments': [{'uri': '/foo/bar-1.ts',
                              'duration': 1500}]}

    assert 1 == len(obj.segments)

    assert 'Segment' == obj.segments[0].__class__.__name__
    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 1500 == obj.segments[0].duration
    assert None == obj.segments[0].title

def test_segments_attribute_without_duration():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'segments': [{'uri': '/foo/bar-1.ts',
                              'title': 'Segment title'}]}


    assert 1 == len(obj.segments)

    assert 'Segment' == obj.segments[0].__class__.__name__
    assert '/foo/bar-1.ts' == obj.segments[0].uri
    assert 'Segment title' == obj.segments[0].title
    assert None == obj.segments[0].duration

def test_is_variant_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'is_variant': False}
    assert not obj.is_variant

    obj.data = {'is_variant': True}
    assert obj.is_variant

def test_playlists_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'playlists': [{'resource': '/url/1.m3u8',
                               'stream_info': {'program_id': '1',
                                               'bandwidth': '320000'}},
                               {'resource': '/url/2.m3u8',
                                'stream_info': {'program_id': '1',
                                                'bandwidth': '120000',
                                                'codecs': 'mp4a.40.5'}},
                                ]}

    assert 2 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].resource
    assert '1' == obj.playlists[0].stream_info.program_id
    assert '320000' == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs

    assert '/url/2.m3u8' == obj.playlists[1].resource
    assert '1' == obj.playlists[1].stream_info.program_id
    assert '120000' == obj.playlists[1].stream_info.bandwidth
    assert 'mp4a.40.5' == obj.playlists[1].stream_info.codecs

def test_playlists_attribute_without_program_id():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'playlists': [{'resource': '/url/1.m3u8',
                               'stream_info': {'bandwidth': '320000'}}
                              ]}

    assert 1 == len(obj.playlists)

    assert '/url/1.m3u8' == obj.playlists[0].resource
    assert '320000' == obj.playlists[0].stream_info.bandwidth
    assert None == obj.playlists[0].stream_info.codecs
    assert None == obj.playlists[0].stream_info.program_id

def test_version_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'version': '2'}
    assert '2' == obj.version


    obj.data = {}
    assert None == obj.version

def test_allow_cache_attribute():
    obj = m3u8.M3U8(SIMPLE_PLAYLIST)
    obj.data = {'allow_cache': 'no'}
    assert 'no' == obj.allow_cache

    obj.data = {}
    assert None == obj.allow_cache
