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
