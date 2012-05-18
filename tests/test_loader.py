import os
import urlparse
import m3u8
from playlists import *

def test_loads_should_create_object_from_string():
    obj = m3u8.loads(SIMPLE_PLAYLIST)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert 'http://media.example.com/entire.ts' == obj.segments[0].uri

def test_load_should_create_object_from_file():
    obj = m3u8.load(SIMPLE_PLAYLIST_FILENAME)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert 'http://media.example.com/entire.ts' == obj.segments[0].uri

def test_load_should_create_object_from_uri():
    obj = m3u8.load(SIMPLE_PLAYLIST_URI)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert 'http://media.example.com/entire.ts' == obj.segments[0].uri

def test_load_should_create_object_from_file_with_relative_segments():
    baseuri = os.path.dirname(RELATIVE_PLAYLIST_FILENAME)
    obj = m3u8.load(RELATIVE_PLAYLIST_FILENAME)
    expected_key_abspath = '%s/key.bin' % os.path.dirname(baseuri)
    expected_key_path = '../key.bin'
    expected_ts1_abspath = '%s/entire1.ts' % baseuri
    expected_ts1_path = '/entire1.ts'
    expected_ts2_abspath = '%s/entire2.ts' % os.path.dirname(baseuri)
    expected_ts2_path = '../entire2.ts'
    expected_ts3_abspath = '%s/entire3.ts' % os.path.dirname(os.path.dirname(baseuri))
    expected_ts3_path = '../../entire3.ts'
    expected_ts4_abspath = '%s/entire4.ts' % baseuri
    expected_ts4_path = 'entire4.ts'

    assert isinstance(obj, m3u8.M3U8)
    assert expected_key_path == obj.key.uri
    assert expected_key_abspath == obj.key.absolute_uri
    assert expected_ts1_path  == obj.segments[0].uri
    assert expected_ts1_abspath  == obj.segments[0].absolute_uri
    assert expected_ts2_path  == obj.segments[1].uri
    assert expected_ts2_abspath  == obj.segments[1].absolute_uri
    assert expected_ts3_path  == obj.segments[2].uri
    assert expected_ts3_abspath  == obj.segments[2].absolute_uri
    assert expected_ts4_path  == obj.segments[3].uri
    assert expected_ts4_abspath  == obj.segments[3].absolute_uri

def test_load_should_create_object_from_uri_with_relative_segments():
    obj = m3u8.load(RELATIVE_PLAYLIST_URI)
    urlparsed = urlparse.urlparse(RELATIVE_PLAYLIST_URI)
    baseuri = os.path.normpath(urlparsed.path + '/..')
    prefix = urlparsed.scheme + '://' + urlparsed.netloc
    expected_key_abspath = '%s%s/key.bin' % (prefix, os.path.normpath(baseuri + '/..'))
    expected_key_path = '../key.bin'
    expected_ts1_abspath = '%s%sentire1.ts' % (prefix, baseuri + '/')
    expected_ts1_path = '/entire1.ts'
    expected_ts2_abspath = '%s%sentire2.ts' % (prefix, os.path.normpath(baseuri + '/..') + '/')
    expected_ts2_path = '../entire2.ts'
    expected_ts3_abspath = '%s%sentire3.ts' % (prefix, os.path.normpath(baseuri + '/../..'))
    expected_ts3_path = '../../entire3.ts'
    expected_ts4_abspath = '%s%sentire4.ts' % (prefix, baseuri + '/')
    expected_ts4_path = 'entire4.ts'

    assert isinstance(obj, m3u8.M3U8)
    assert expected_key_path == obj.key.uri
    assert expected_key_abspath == obj.key.absolute_uri
    assert expected_ts1_path  == obj.segments[0].uri
    assert expected_ts1_abspath  == obj.segments[0].absolute_uri
    assert expected_ts2_path  == obj.segments[1].uri
    assert expected_ts2_abspath  == obj.segments[1].absolute_uri
    assert expected_ts3_path  == obj.segments[2].uri
    assert expected_ts3_abspath  == obj.segments[2].absolute_uri
    assert expected_ts4_path  == obj.segments[3].uri
    assert expected_ts4_abspath  == obj.segments[3].absolute_uri
